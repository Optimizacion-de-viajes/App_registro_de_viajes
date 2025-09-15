import datetime
import json
import os
import io
import threading
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout

# Importar las librerías de Google
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Importar jnius solo si se está en Android
if platform == 'android':
    from jnius import autoclass

# Define los permisos (scopes) necesarios para acceder a Google Drive
ALCANCES = ['https://www.googleapis.com/auth/drive.file']
Window.clearcolor = (0.9, 0.9, 0.9, 1)

class ManejadorGoogleDrive:
    """
    Clase para manejar la autenticación y la subida a Google Drive.
    """
    def __init__(self, app_instance):
        self.credenciales = None
        self.archivo_token = 'token.json'
        self.archivo_credenciales = 'client_secret_742107307448-5maldnumc103gcs45r02bnirjs62820h.apps.googleusercontent.com.json'
        self.app_instance = app_instance
        self.servicio = None

    def autenticar(self):
        """
        Maneja el flujo de autenticación de OAuth 2.0 para escritorio y Android.
        """
        if os.path.exists(self.archivo_token):
            self.credenciales = Credentials.from_authorized_user_file(self.archivo_token, ALCANCES)

        if not self.credenciales or not self.credenciales.valid:
            if self.credenciales and self.credenciales.expired and self.credenciales.refresh_token:
                try:
                    self.credenciales.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    self.credenciales = None
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.archivo_credenciales, ALCANCES)
                except FileNotFoundError:
                    print(f"Error: No se encontró el archivo de credenciales '{self.archivo_credenciales}'.")
                    return
                except Exception as e:
                    print(f"Error cargando el archivo de credenciales: {e}")
                    return

                if platform == 'android':
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    auth_url, _ = flow.authorization_url(prompt='consent')

                    try:
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        Intent = autoclass('android.content.Intent')
                        Uri = autoclass('android.net.Uri')
                        intent = Intent(Intent.ACTION_VIEW, Uri.parse(auth_url))
                        PythonActivity.getCurrentActivity().startActivity(intent)
                        print("Por favor, autentíquese en su navegador y pegue el código de autorización.")
                        self.mostrar_popup_codigo(flow)
                        return
                    except Exception as e:
                        print(f"Error abriendo el navegador en Android: {e}")
                        return
                else: # Flujo de escritorio
                    self.credenciales = flow.run_local_server(port=0, success_message="Autenticación completada. Puedes cerrar esta ventana.")

        if self.credenciales:
            try:
                with open(self.archivo_token, 'w') as token:
                    token.write(self.credenciales.to_json())
                print("Credenciales guardadas con éxito.")
                self.servicio = build('drive', 'v3', credentials=self.credenciales)
            except Exception as e:
                print(f"Error al guardar las credenciales o construir el servicio: {e}")

    def mostrar_popup_codigo(self, flow):
        """
        Muestra un popup para que el usuario pegue el código de autorización en Android.
        """
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        etiqueta = Label(text="Pegue el código de autorización de Google aquí:", halign='center', size_hint_y=None, height=dp(40))
        campo_texto = TextInput(hint_text="Código de autorización", multiline=False, size_hint_y=None, height=dp(40))

        def intercambiar_codigo_y_cerrar(instance):
            code = campo_texto.text.strip()
            if code:
                try:
                    flow.fetch_token(code=code)
                    self.credenciales = flow.credentials
                    with open(self.archivo_token, 'w') as token:
                        token.write(self.credenciales.to_json())
                    self.servicio = build('drive', 'v3', credentials=self.credenciales)
                    print("Autenticación exitosa en Android.")
                except Exception as e:
                    print(f"Error al obtener token con el código: {e}")
                finally:
                    popup.dismiss()

        btn_aceptar = Button(text="Aceptar", size_hint_y=None, height=dp(40))
        btn_aceptar.bind(on_release=intercambiar_codigo_y_cerrar)

        contenido.add_widget(etiqueta)
        contenido.add_widget(campo_texto)
        contenido.add_widget(btn_aceptar)

        popup = Popup(title='Autenticación de Google Drive', content=contenido, size_hint=(0.9, 0.4))
        popup.open()

    def subir_archivo(self, ruta_archivo, nombre_archivo_drive):
        """
        Sube un archivo local a Google Drive, actualizándolo si ya existe.
        """
        if not self.servicio:
            self.autenticar()

        if not self.servicio:
            print("Error: El servicio de Google Drive no está disponible.")
            return

        try:
            resultados = self.servicio.files().list(
                q=f"name='{nombre_archivo_drive}' and trashed=false",
                fields="nextPageToken, files(id)").execute()
            elementos = resultados.get('files', [])

            metadatos_archivo = {'name': nombre_archivo_drive}
            medio = MediaFileUpload(ruta_archivo, mimetype='application/json')

            if elementos:
                id_archivo = elementos[0]['id']
                self.servicio.files().update(
                    fileId=id_archivo,
                    media_body=medio,
                    fields='id').execute()
                print(f"Archivo actualizado en Drive, ID: {id_archivo}")
            else:
                archivo = self.servicio.files().create(
                    body=metadatos_archivo,
                    media_body=medio,
                    fields='id').execute()
                print(f"Archivo subido a Drive, ID: {archivo.get('id')}")
        except Exception as error:
            print(f'Ocurrió un error al subir el archivo: {error}')

class AppRegistroTiempos(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nombre_archivo_drive = "datos.json"
        self.manejador_drive = ManejadorGoogleDrive(self)
        self.hora_inicio = None
        self.hora_fin = None

        # Carga los datos al iniciar la aplicación
        self.datos = self.cargar_datos_locales()

    def cargar_datos_locales(self):
        """
        Carga los datos desde el archivo JSON local o crea uno nuevo si no existe.
        """
        try:
            with open(self.nombre_archivo_drive, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
                # Verifica que las claves esenciales existan
                if "vehiculos" not in datos or "puntos_intermedios" not in datos or "datos guardados" not in datos:
                    raise json.JSONDecodeError("Formato de archivo JSON incorrecto", "datos.json", 0)
                return datos
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar 'datos.json': {e}. Creando archivo con datos por defecto.")
            datos_default = {
                "vehiculos": ["Caminando", "Carro"],
                "puntos_intermedios": [{"nombre": "Ninguno", "coordenadas": {"latitud": 0, "longitud": 0}}],
                "datos guardados": []
            }
            # Guarda el nuevo archivo por defecto
            with open(self.nombre_archivo_drive, "w", encoding="utf-8") as archivo:
                json.dump(datos_default, archivo, indent=4)
            return datos_default

    def build(self):
        self.vehiculos = self.datos["vehiculos"]
        self.puntos_intermedios = [punto["nombre"] for punto in self.datos["puntos_intermedios"]]
        self.datos_guardados = self.datos["datos guardados"]

        layout_principal = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        # Sección 1: Vehículos
        seccion1 = MDBoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10), padding=dp(5),
                                 orientation='horizontal', md_bg_color=(0.9, 0.9, 0.9, 1))
        etiqueta_vehiculos = Label(text="Vehículos", font_size=sp(20), size_hint_x=0.4,
                                   halign='left', valign='middle', color=(0.1, 0.1, 0.1, 1))
        self.selector_vehiculos = Spinner(
            text=self.vehiculos[0],
            values=self.vehiculos,
            size_hint_x=0.6,
            font_size=sp(18),
            background_normal='',
            background_color=(0.6, 0.8, 1, 1)
        )
        seccion1.add_widget(etiqueta_vehiculos)
        seccion1.add_widget(self.selector_vehiculos)

        # Sección 2: Agregar Vehículo
        seccion2 = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        btn_agregar = Button(text="Agregar Vehículo", font_size=sp(18), background_normal='',
                                   background_color=(0.3, 0.7, 0.5, 1))
        btn_agregar.bind(on_release=self.mostrar_popup_agregar_vehiculo)
        seccion2.add_widget(btn_agregar)

        # Sección 3: Origen y Destino
        seccion3 = GridLayout(cols=2, size_hint_y=None, height=dp(70), padding=dp(5), spacing=dp(10))
        # Etiquetas de Origen y Destino añadidas
        etiqueta_origen = Label(text="Origen", halign='left', valign='middle', color=(0.1, 0.1, 0.1, 1))
        self.selector_origen = Spinner(
            text=self.puntos_intermedios[0],
            values=self.puntos_intermedios,
            font_size=sp(16),
            background_normal='',
            background_color=(0, 0, 1, 1)
        )
        etiqueta_destino = Label(text="Destino", halign='left', valign='middle', color=(0.1, 0.1, 0.1, 1))
        self.selector_destino = Spinner(
            text=self.puntos_intermedios[0],
            values=self.puntos_intermedios,
            font_size=sp(16),
            background_normal='',
            background_color=(0, 0, 1, 1)
        )
        seccion3.add_widget(etiqueta_origen)
        seccion3.add_widget(self.selector_origen)
        seccion3.add_widget(etiqueta_destino)
        seccion3.add_widget(self.selector_destino)

        # Sección de Puntos Intermedios
        seccion_intermedia = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        self.btn_intermedio = Button(text="Añadir Puntos Intermedios", font_size=sp(18), background_normal='',
                                     background_color=(0.5, 0.5, 0.9, 1))
        self.btn_intermedio.bind(on_release=self.mostrar_popup_agregar_punto)
        seccion_intermedia.add_widget(self.btn_intermedio)

        # Sección 4: Inicio/Fin
        seccion4 = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(5))
        self.btn_inicio_fin = Button(text="Inicio", font_size=sp(24), background_normal='',
                                     background_color=(0.2, 0.6, 0.8, 1))
        self.btn_inicio_fin.bind(on_release=self.alternar_inicio_fin)
        seccion4.add_widget(self.btn_inicio_fin)

        # Sección 5: Resumen
        seccion5 = BoxLayout(size_hint_y=None, height=dp(150), padding=dp(5))
        self.etiqueta_resumen = Label(text="Resumen:", font_size=sp(16), halign='left',
                                     valign='top', text_size=(Window.width - dp(20), None),
                                     color=(0.1, 0.1, 0.1, 1))
        seccion5.add_widget(self.etiqueta_resumen)

        # Sección 6: Modificar y Eliminar
        seccion6 = GridLayout(cols=2, size_hint_y=None, height=dp(70), padding=dp(5), spacing=dp(10))
        btn_modificar = Button(text="Modificar Último", font_size=sp(18), background_normal='',
                                     background_color=(0.9, 0.7, 0.2, 1))
        btn_modificar.bind(on_release=self.mostrar_popup_modificar)
        btn_eliminar = Button(text="Eliminar", font_size=sp(18), background_normal='',
                                     background_color=(0.9, 0.4, 0.4, 1))
        btn_eliminar.bind(on_release=self.eliminar_datos)
        seccion6.add_widget(btn_modificar)
        seccion6.add_widget(btn_eliminar)

        # Botón para subir a Drive
        btn_subir = Button(text="Subir a Drive", font_size=sp(18), background_normal='', background_color=(0.1, 0.5, 0.9, 1))
        btn_subir.bind(on_release=self.subir_a_drive)

        # Botón para autenticar con Google Drive
        btn_autenticar = Button(text="Autenticar con Drive", font_size=sp(18), background_normal='', background_color=(0.1, 0.9, 0.5, 1))
        btn_autenticar.bind(on_release=lambda x: threading.Thread(target=self.manejador_drive.autenticar).start())


        layout_principal.add_widget(seccion1)
        layout_principal.add_widget(seccion2)
        layout_principal.add_widget(seccion3)
        layout_principal.add_widget(seccion_intermedia)
        layout_principal.add_widget(seccion4)
        layout_principal.add_widget(seccion5)
        layout_principal.add_widget(seccion6)
        layout_principal.add_widget(btn_subir)
        layout_principal.add_widget(btn_autenticar)

        self.actualizar_resumen()

        return layout_principal
    def alternar_inicio_fin(self, instance):
        if self.btn_inicio_fin.text == "Inicio":
            # Si el botón dice "Inicio", significa que estamos comenzando un viaje.
            self.hora_inicio = datetime.datetime.now()
            self.btn_inicio_fin.text = "Fin"
            self.actualizar_resumen()
            print("Viaje iniciado.")

        elif self.btn_inicio_fin.text == "Fin":
            # Si el botón dice "Fin", significa que estamos terminando un viaje.
            self.hora_fin = datetime.datetime.now()

            # Recopila los datos del viaje.
            datos_viaje = {
                "vehiculo": self.selector_vehiculos.text,
                "origen": self.selector_origen.text,
                "destino": self.selector_destino.text,
                "hora_inicio": self.hora_inicio.strftime('%Y-%m-%d %H:%M:%S'),
                "hora_fin": self.hora_fin.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Agrega los datos al listado.
            self.datos["datos guardados"].append(datos_viaje)

            # Llama a la función para guardar el JSON.
            self.guardar_json()

            # Reinicia las variables de tiempo y el texto del botón.
            self.hora_inicio = None
            self.hora_fin = None
            self.btn_inicio_fin.text = "Inicio"
            self.actualizar_resumen()
            print("Viaje finalizado y datos guardados.")

    def mostrar_popup_agregar_vehiculo(self, instance):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        campo_texto = TextInput(hint_text="Nombre del vehículo", size_hint_y=None, height=dp(40))
        def agregar_y_cerrar(instance):
            if campo_texto.text and campo_texto.text not in self.vehiculos:
                self.vehiculos.append(campo_texto.text)
                self.datos["vehiculos"].append(campo_texto.text)
                self.guardar_json()
                self.selector_vehiculos.values = self.vehiculos
                self.selector_vehiculos.text = campo_texto.text
            popup.dismiss()
        btn_agregar = Button(text="Añadir", size_hint_y=None, height=dp(40))
        btn_agregar.bind(on_release=agregar_y_cerrar)
        contenido.add_widget(campo_texto)
        contenido.add_widget(btn_agregar)
        popup = Popup(title='Agregar Nuevo Vehículo', content=contenido, size_hint=(0.8, 0.3))
        popup.open()

    def mostrar_popup_agregar_punto(self, instance):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        etiqueta_nombre = Label(text="Nombre del punto:")
        campo_nombre = TextInput(hint_text="Ej. Mi Casa", size_hint_y=None, height=dp(40))
        etiqueta_latitud = Label(text="Latitud:")
        campo_latitud = TextInput(hint_text="Ej. 25.6866142", input_filter='float', size_hint_y=None, height=dp(40))
        etiqueta_longitud = Label(text="Longitud:")
        campo_longitud = TextInput(hint_text="Ej. -100.3161126", input_filter='float', size_hint_y=None, height=dp(40))
        def agregar_y_cerrar(instance):
            nombre = campo_nombre.text
            try:
                latitud = float(campo_latitud.text)
                longitud = float(campo_longitud.text)
                if nombre and nombre not in self.puntos_intermedios:
                    self.puntos_intermedios.append(nombre)
                    nuevo_punto = {"nombre": nombre, "coordenadas": {"latitud": latitud, "longitud": longitud}}
                    self.datos["puntos_intermedios"].append(nuevo_punto)
                    self.guardar_json()
                    self.selector_origen.values = self.puntos_intermedios
                    self.selector_destino.values = self.puntos_intermedios
                popup.dismiss()
            except ValueError:
                error_popup = Popup(title='Error', content=Label(text='Las coordenadas deben ser números.'), size_hint=(0.7, 0.2))
                error_popup.open()
        btn_agregar = Button(text="Añadir Punto", size_hint_y=None, height=dp(40))
        btn_agregar.bind(on_release=agregar_y_cerrar)
        contenido.add_widget(etiqueta_nombre)
        contenido.add_widget(campo_nombre)
        contenido.add_widget(etiqueta_latitud)
        contenido.add_widget(campo_latitud)
        contenido.add_widget(etiqueta_longitud)
        contenido.add_widget(campo_longitud)
        contenido.add_widget(btn_agregar)
        popup = Popup(title='Agregar Nuevo Punto Intermedio', content=contenido, size_hint=(0.9, 0.7))
        popup.open()

    def guardar_datos(self):
        if self.hora_inicio and self.hora_fin:
            datos = {
                "vehiculo": self.selector_vehiculos.text,
                "origen": self.selector_origen.text,
                "destino": self.selector_destino.text,
                "hora_inicio": self.hora_inicio.strftime('%Y-%m-%d %H:%M:%S'),
                "hora_fin": self.hora_fin.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.datos_guardados.append(datos)
            self.datos["datos guardados"].append(datos)
            self.guardar_json()
            self.hora_inicio = None
            self.hora_fin = None
            self.actualizar_resumen()

    def actualizar_resumen(self):
        texto_resumen = "Resumen:\n"
        if self.hora_inicio:
            texto_resumen += f"Inicio: {self.hora_inicio.strftime('%H:%M:%S')}\n"
        if self.datos_guardados:
            ultimo_dato = self.datos_guardados[-1]
            texto_resumen += f"\nÚltimo Dato Guardado:\n"
            texto_resumen += f"[{len(self.datos_guardados)}] {ultimo_dato['vehiculo']} ({ultimo_dato['origen']} -> {ultimo_dato['destino']})\n"
            texto_resumen += f"      Inicio: {ultimo_dato['hora_inicio']} - Fin: {ultimo_dato['hora_fin']}\n"
        else:
            texto_resumen += "\nNo hay datos guardados.\n"
        self.etiqueta_resumen.text = texto_resumen

    def mostrar_popup_modificar(self, instance):
        if not self.datos_guardados:
            return
        ultimo_dato = self.datos_guardados[-1]
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        etiqueta_vehiculo = Label(text="Vehículo", size_hint_y=None, height=dp(30))
        selector_vehiculo = Spinner(
            text=ultimo_dato['vehiculo'], values=self.vehiculos, size_hint_y=None, height=dp(40)
        )
        etiqueta_origen = Label(text="Origen", size_hint_y=None, height=dp(30))
        selector_origen = Spinner(
            text=ultimo_dato['origen'], values=self.puntos_intermedios, size_hint_y=None, height=dp(40)
        )
        etiqueta_destino = Label(text="Destino", size_hint_y=None, height=dp(30))
        selector_destino = Spinner(
            text=ultimo_dato['destino'], values=self.puntos_intermedios, size_hint_y=None, height=dp(40)
        )
        def modificar_y_cerrar(instance):
            self.datos_guardados[-1]['vehiculo'] = selector_vehiculo.text
            self.datos_guardados[-1]['origen'] = selector_origen.text
            self.datos_guardados[-1]['destino'] = selector_destino.text
            self.guardar_json()
            self.actualizar_resumen()
            popup.dismiss()
        btn_guardar = Button(text="Guardar Cambios", size_hint_y=None, height=dp(40))
        btn_guardar.bind(on_release=modificar_y_cerrar)
        contenido.add_widget(etiqueta_vehiculo)
        contenido.add_widget(selector_vehiculo)
        contenido.add_widget(etiqueta_origen)
        contenido.add_widget(selector_origen)
        contenido.add_widget(etiqueta_destino)
        contenido.add_widget(selector_destino)
        contenido.add_widget(btn_guardar)
        popup = Popup(title='Modificar Últimos Datos', content=contenido, size_hint=(0.9, 0.7))
        popup.open()

    def eliminar_datos(self, instance):
        if self.datos_guardados:
            self.datos_guardados.pop()
            self.guardar_json()
        self.actualizar_resumen()

    def guardar_json(self):
        """
        Guarda el archivo JSON local y lo sube a Google Drive en un hilo secundario.
        """
        with open(self.nombre_archivo_drive, "w", encoding="utf-8") as archivo:
            json.dump(self.datos, archivo, indent=4)
        print("Datos guardados localmente. Iniciando subida a Drive...")
        threading.Thread(target=self.manejador_drive.subir_archivo,
                          args=(self.nombre_archivo_drive, self.nombre_archivo_drive)).start()

    def subir_a_drive(self, instance):
        """
        Función para subir el archivo 'datos.json' a Google Drive.
        """
        threading.Thread(target=self.manejador_drive.subir_archivo,
                          args=(self.nombre_archivo_drive, self.nombre_archivo_drive)).start()
        print("Subiendo 'datos.json' a Google Drive...")

if __name__ == '__main__':
    AppRegistroTiempos().run()
