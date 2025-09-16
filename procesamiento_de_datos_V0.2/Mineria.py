import numpy as np
import os
import pandas as pd
import re

#Abrir archivo de datos
with open('Belinda.txt', 'r', encoding='utf-8') as file:
    lines = [line.strip() for line in file.readlines()]
df = pd.DataFrame(lines, columns=['text'])

#Filtrar mensajes humanos
valid_rows = []
for index, row in df.iterrows():
    if re.match(r'\d{1,2}/\d{1,2}/\d{1,4}, \d{2}:\d{2} - .+:.+', row['text']):
        valid_rows.append(row)
df_filtrado = pd.DataFrame(valid_rows)
dates = []
times = []
names = []
messages = []

#Separar información del mensaje
for index, row in df_filtrado.iterrows():
    match = re.match(r'(\d{1,2}/\d{1,2}/\d{1,4}), (\d{2}:\d{2}) - (.+?): (.*)', row['text'])
    if match:
        dates.append(match.group(1))
        times.append(match.group(2))
        names.append(match.group(3))
        messages.append(match.group(4))
    else:
        dates.append(None)
        times.append(None)
        names.append(None)
        messages.append(None)

df_filtrado['date'] = dates
df_filtrado['time'] = times
df_filtrado['nametag'] = names
df_filtrado['message'] = messages
df_filtrado = df_filtrado.drop('text', axis=1)

#Limpieza de datos
def nombre_unico(texto):
    emoji=re.compile('[\U0001F921\u2763\ufe0f]+',flags=re.UNICODE)
    unico=emoji.sub(r'',texto)
    return unico.strip().split()[0]

df_filtrado['name'] = df_filtrado['nametag'].apply(nombre_unico)
df_filtrado = df_filtrado.drop('nametag', axis=1)
df_filtrado = df_filtrado[~df_filtrado['message'].str.contains('you deleted this message', case=False, na=False)]
df_filtrado = df_filtrado[~df_filtrado['message'].str.contains('Se eliminó este mensaje.', case=False, na=False)]

#Transformar formato de 12 horas a 24 horas
hora = []
for index, row in df_filtrado.iterrows():
    match = re.search(r'\b(\d{1,2}:\d{1,2}:\d{1,2}(?:\s?hrs?))\b', row['message'])
    match2 = re.search(r'\b(\d{1,2}:\d{1,2}[ap]\.m\.)', row['message'])
    if match:
        match =re.findall(r'\b(\d{1,2}:\d{1,2}:\d{1,2})\s*hrs', row['message'])
        hora.append(match[0])
    else:
        if match2:
            match3 = re.search(r'(\d{1,2}):(\d{1,2})(a\.m\.|p\.m\.)', row['message'])
            HH = int(match3.group(1))
            MM = int(match3.group(2))
            am_pm = match3.group(3)
            if am_pm == 'p.m.' and HH != 12:
                HH += 12
            elif am_pm == 'a.m.' and HH == 12:
                HH = 0
            hora.append(f'{HH:02d}:{MM:02d}:00')
        else:
            hora.append(None)

df_filtrado['hour'] = hora
df_filtrado = df_filtrado.drop('time', axis=1)
df_filtrado['date'] = pd.to_datetime(df_filtrado['date'], errors='coerce')
df_filtrado['date'] = df_filtrado['date'].dt.strftime('%d/%m/%y')

#Filtro de vehiculo usado
vehiculo = ["m1", "m2", "m3", "ruta 601", "ruta 107", "didi", "carro", "ruta nuevo león san bernabé",
            "ruta nuevo león talleres","ruta 185 zertuche","ruta 185 20 nov","transmetro pablo livas"]
df_filtrado['vehicle'] = None
for index, row in df_filtrado.iterrows():
    for keyword in vehiculo:
        if keyword in str(row['message']).lower():
            df_filtrado.loc[index, 'vehicle'] = keyword
            break

#Filtro de paradas y estaciones usados
lugar = ["talleres san sernabe", "benabe", "unidad modelo", "modelo aztlán", "aztlan", "penitenciaría", "penitenciaria",
         "alfonso reyes", "mitras", "simon bolibar", "simón bolivar", "hospital", "edison", "central", "cuauhtémoc",
         "cuauhtemoc", "del golfo", "felix u gómez", "félix u gomez", "félix u gómez", "felix u gomez",
         "parque fundidora", "fundidora", "\"y\" griega,", "y griega", "eloy cavazos", "lerdo de tejada", "exposición",
         "exposicion", "casa", "sendero", "tapia", "san nicolas", "anahuac", "cu", "universidad", "niños heroes",
         "regina", "general anaya", "cuauhtemoc", "p. alameda", "p alameda", "fundadores", "padre mier",
         "general i.zaragoza", "general i zaragoza", "general zaragoza", "hospital metropolitano", "los angeles",
         "ruiz cortinez", "col. moderna", "metalurgia", "col. obrera", "santa lucia", "general i.zaragoza",
         "general i zaragoza", "optica omega", "p1", "p2", "p3", " 3.14159265 alameda", "3.1415 alameda",
         "3.1416 alameda", "3.141592 alameda", "3.14 alameda", "3.1415926535 alameda", "smart", "smart garcía",
         "smart garcia", "c. praderas de iturbide", "p. urbivilla", "soriana cercano a mitras", "gimnasio sias",
         "estacion", "base", "soriana mercado", "presidencia", "estación", "san bernabé", "salí", "óptica omega",
         "soriana", "niños héroes", "2° oxxo de sierra", "alameda", "sun mall guadalupe"]

df_filtrado['place'] = None
for index, row in df_filtrado.iterrows():
    for keyword in lugar:
        if keyword in str(row['message']).lower():
            if df_filtrado.loc[index, 'vehicle'] is None:
                if "detuvo" in str(row['message']).lower():
                    df_filtrado.loc[index, 'place'] = None
                    break
                else:
                    if keyword == "salí" or keyword == "sali":
                        df_filtrado.loc[index, 'place'] = "casa"
                        break
                    match keyword:
                        
                        case "p. alameda":
                            df_filtrado.loc[index, 'place'] = "p1. alameda"
                            break
                        case "p1":
                            df_filtrado.loc[index, 'place'] = "p1. alameda"
                            break
                        case "p2":
                            df_filtrado.loc[index, 'place'] = "p2. alameda"
                            break
                        case "p3":
                            df_filtrado.loc[index, 'place'] = "p3. alameda"
                            break
                        case "3.14159265 alameda":
                            df_filtrado.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.1416 alameda":
                            df_filtrado.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.141592 alameda":
                            df_filtrado.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.14 alameda":
                            df_filtrado.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.1415926535 alameda":
                            df_filtrado.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "cuauhtemoc":
                            df_filtrado.loc[index, 'place'] = "cuauhtémoc"
                            break
                    df_filtrado.loc[index, 'place'] = keyword
                    break

#Creación de marca de clase
class_mark_list = []
for index, row in df_filtrado.iterrows():
    h = row['hour']
    try:
        minuto = int(h[3:5])
        marca_clase = f"{h[:3]}{minuto//5*5:02d}:00"
        class_mark_list.append(marca_clase)
    except:
        class_mark_list.append(None)
df_filtrado['class mark'] = class_mark_list

#Ordenar columnas y guardar datos en archivo de excel
lita=['date','name','hour','class mark','place','vehicle','message']
df_filtrado=df_filtrado[lita]

df_filtrado.to_excel('informacion.xlsx', index=False)
print(df_filtrado)