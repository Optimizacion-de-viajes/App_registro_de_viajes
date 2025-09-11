import datetime
import json
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout

# Establece el tamaño de la ventana para simular un dispositivo móvil
Window.size = (400, 700)
Window.clearcolor = (0.9, 0.9, 0.9, 1)

class AppRegistroTiempos(MDApp):
    # Carga el archivo JSON al iniciar la aplicación
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            with open("datos.json", "r", encoding="utf-8") as archivo:
                self.datos = json.load(archivo)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar 'datos.json': {e}. Se creará un archivo con datos por defecto.")
            self.datos = {
                "vehiculos": ["Caminando", "Carro"],
                "puntos_intermedios": [{"nombre": "Ninguno", "coordenadas": {"latitud": 0, "longitud": 0}}],
                "datos guardados": []
            }
            self.guardar_json()

    def build(self):
        print("hola mundo")
        self.vehiculos = self.datos["vehiculos"]
        self.puntos_intermedios = [punto["nombre"] for punto in self.datos["puntos_intermedios"]]

        self.hora_inicio = None
        self.hora_fin = None
        self.datos_guardados = self.datos["datos guardados"]

        layout_principal = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        seccion1 = MDBoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10), padding=dp(5),
                               orientation='horizontal', md_bg_color=(0.9, 0.9, 0.9, 1))

        etiqueta_vehiculos = Label(text="Vehículos", font_size='20sp', size_hint_x=0.4,
                                   halign='left', valign='middle', color=(0.1, 0.1, 0.1, 1))

        self.selector_vehiculos = Spinner(
            text=self.vehiculos[0],
            values=self.vehiculos,
            size_hint_x=0.6,
            font_size='18sp',
            background_normal='',
            background_color=(0.6, 0.8, 1, 1)
        )
        seccion1.add_widget(etiqueta_vehiculos)
        seccion1.add_widget(self.selector_vehiculos)

        seccion2 = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        btn_agregar = Button(text="Agregar Vehículo", font_size='18sp', background_normal='',
                             background_color=(0.3, 0.7, 0.5, 1))
        btn_agregar.bind(on_release=self.mostrar_popup_agregar_vehiculo)
        seccion2.add_widget(btn_agregar)

        seccion3 = GridLayout(cols=2, size_hint_y=None, height=dp(70), padding=dp(5), spacing=dp(10))
        self.selector_origen = Spinner(
            text=self.puntos_intermedios[0],
            values=self.puntos_intermedios,
            font_size='16sp',
            background_normal='',
            background_color=(0.8, 0.9, 1, 1)
        )
        self.selector_destino = Spinner(
            text=self.puntos_intermedios[0],
            values=self.puntos_intermedios,
            font_size='16sp',
            background_normal='',
            background_color=(0.8, 0.9, 1, 1)
        )
        seccion3.add_widget(self.selector_origen)
        seccion3.add_widget(self.selector_destino)

        seccion_intermedia = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        self.btn_intermedio = Button(text="Añadir Puntos Intermedios", font_size='18sp', background_normal='',
                                     background_color=(0.5, 0.5, 0.9, 1))
        self.btn_intermedio.bind(on_release=self.mostrar_popup_agregar_punto)
        seccion_intermedia.add_widget(self.btn_intermedio)

        seccion4 = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(5))
        self.btn_inicio_fin = Button(text="Inicio", font_size='24sp', background_normal='',
                                     background_color=(0.2, 0.6, 0.8, 1))
        self.btn_inicio_fin.bind(on_release=self.alternar_inicio_fin)
        seccion4.add_widget(self.btn_inicio_fin)

        seccion5 = BoxLayout(size_hint_y=None, height=dp(150), padding=dp(5))
        self.etiqueta_resumen = Label(text="Resumen:", font_size='16sp', halign='left',
                                     valign='top', text_size=(Window.width - dp(20), None),
                                     color=(0.1, 0.1, 0.1, 1))
        seccion5.add_widget(self.etiqueta_resumen)

        seccion6 = GridLayout(cols=2, size_hint_y=None, height=dp(70), padding=dp(5), spacing=dp(10))
        btn_modificar = Button(text="Modificar Último", font_size='18sp', background_normal='',
                               background_color=(0.9, 0.7, 0.2, 1))
        btn_modificar.bind(on_release=self.mostrar_popup_modificar)
        btn_eliminar = Button(text="Eliminar", font_size='18sp', background_normal='',
                              background_color=(0.9, 0.4, 0.4, 1))
        btn_eliminar.bind(on_release=self.eliminar_datos)
        seccion6.add_widget(btn_modificar)
        seccion6.add_widget(btn_eliminar)

        layout_principal.add_widget(seccion1)
        layout_principal.add_widget(seccion2)
        layout_principal.add_widget(seccion3)
        layout_principal.add_widget(seccion_intermedia)
        layout_principal.add_widget(seccion4)
        layout_principal.add_widget(seccion5)
        layout_principal.add_widget(seccion6)

        self.actualizar_resumen()

        return layout_principal

    def guardar_json(self):
        """Guarda el diccionario de datos en el archivo datos.json."""
        with open("datos.json", "w", encoding="utf-8") as archivo:
            json.dump(self.datos, archivo, indent=4)

    def alternar_inicio_fin(self, instance):
        """
        Alterna el texto del botón 'Inicio'/'Fin' y registra la hora.
        """
        if self.btn_inicio_fin.text == "Inicio":
            self.hora_inicio = datetime.datetime.now()
            self.btn_inicio_fin.text = "Fin"
        elif self.btn_inicio_fin.text == "Fin":
            self.hora_fin = datetime.datetime.now()
            self.btn_inicio_fin.text = "Inicio"
            self.guardar_datos()
            self.actualizar_resumen()

    def mostrar_popup_agregar_vehiculo(self, instance):
        """
        Muestra un popup para agregar un nuevo vehículo a la lista.
        """
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

        popup = Popup(title='Agregar Nuevo Vehículo', content=contenido,
                      size_hint=(0.8, 0.3))
        popup.open()

    def mostrar_popup_agregar_punto(self, instance):
        """
        Muestra un popup para agregar un nuevo punto intermedio con coordenadas.
        """
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        etiqueta_nombre = Label(text="Nombre del punto:")
        campo_nombre = TextInput(hint_text="Ej. Mi Casa", size_hint_y=None, height=dp(40))

        etiqueta_latitud = Label(text="Latitud (primer valor de Google Maps):")
        campo_latitud = TextInput(hint_text="Ej. 25.6866142", input_filter='float', size_hint_y=None, height=dp(40))

        etiqueta_longitud = Label(text="Longitud (segundo valor de Google Maps):")
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
                # Mostrar un mensaje de error si las coordenadas no son números válidos
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

        popup = Popup(title='Agregar Nuevo Punto Intermedio', content=contenido,
                      size_hint=(0.9, 0.7))
        popup.open()

    def guardar_datos(self):
        """
        Guarda toda la información de la sesión en la lista de datos guardados y en el archivo.
        """
        if self.hora_inicio and self.hora_fin:
            datos = {
                "vehiculo": self.selector_vehiculos.text,
                "origen": self.selector_origen.text,
                "destino": self.selector_destino.text,
                "hora_inicio": self.hora_inicio.strftime('%Y-%m-%d %H:%M:%S'),
                "hora_fin": self.hora_fin.strftime('%Y-%m-%d %H:%M:%S')
            }
            # Añade los datos tanto a la lista temporal como a la del diccionario principal
            self.datos_guardados.append(datos)
            self.datos["datos guardados"].append(datos)
            self.guardar_json()

            self.hora_inicio = None
            self.hora_fin = None
        self.actualizar_resumen()

    def actualizar_resumen(self):
        """
        Actualiza el Label de resumen con la información actual y guardada.
        """
        texto_resumen = "Resumen:\n"
        if self.hora_inicio:
            texto_resumen += f"Inicio: {self.hora_inicio.strftime('%H:%M:%S')}\n"

        texto_resumen += f"Vehículo: {self.selector_vehiculos.text}\n"
        texto_resumen += f"Origen: {self.selector_origen.text}\n"
        texto_resumen += f"Destino: {self.selector_destino.text}\n"

        texto_resumen += "\nDatos Guardados:\n"
        if self.datos_guardados:
            # Invierte la lista para mostrar los datos más recientes primero
            for i, datos in enumerate(reversed(self.datos_guardados)):
                texto_resumen += f"[{len(self.datos_guardados)-i}] {datos['vehiculo']} ({datos['origen']} -> {datos['destino']})\n"
                texto_resumen += f"    Inicio: {datos['hora_inicio']} - Fin: {datos['hora_fin']}\n"
        else:
            texto_resumen += "No hay datos guardados.\n"

        self.etiqueta_resumen.text = texto_resumen

    def mostrar_popup_modificar(self, instance):
        """
        Muestra un popup para modificar los últimos datos guardados.
        """
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
        """
        Elimina el último dato guardado y actualiza el archivo JSON.
        """
        if self.datos_guardados:
            self.datos_guardados.pop()
            self.datos["datos guardados"].pop()
            self.guardar_json()
        self.actualizar_resumen()

if __name__ == '__main__':
    AppRegistroTiempos().run()
