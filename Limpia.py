import pandas as pd
import re
import openpyxl
import datetime
import numpy as np

with open('EKKAP.txt', 'r', encoding='utf-8') as file:
    lines = [line.strip() for line in file.readlines()]

df = pd.DataFrame(lines, columns=['text'])

valid_rows = []
for index, row in df.iterrows():
    if re.match(r'\d{1,2}/\d{1,2}/\d{1,4}, \d{2}:\d{2} - .+:.+', row['text']):
        valid_rows.append(row)
df_filtered = pd.DataFrame(valid_rows)
dates = []
times = []
names = []
messages = []

for index, row in df_filtered.iterrows():
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

df_filtered['date'] = dates
df_filtered['time'] = times
df_filtered['name'] = names
df_filtered['message'] = messages
df_filtered = df_filtered.drop('text', axis=1)
df_filtered = df_filtered[df_filtered['name'] == 'EKKAP']
#df_filtered = df_filtered.drop([7, 8, 9])
df_filtered = df_filtered.drop('time', axis=1)
hora = []
for index, row in df_filtered.iterrows():
    match = re.search(r'\b(\d{1,2}:\d{1,2}:\d{1,2}(?:\s?hrs?))\b', row['message'])
    match2 = re.search(r'\b(\d{1,2}:\d{1,2}[ap]\.m\.)', row['message'])
    if match:
        hora.append(match.group(1))
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

df_filtered['hour'] = hora

df_filtered['hour'] = df_filtered['hour'].astype(str)
class_mark_list = []
for index, row in df_filtered.iterrows():
    h = row['hour']
    try:
        minuto = int(h[3:5])
        marca_clase = f"{h[:3]}{minuto//5*5:02d}:00"
        class_mark_list.append(marca_clase)
    except:
        class_mark_list.append(None)
df_filtered['class mark'] = class_mark_list

apoyo = ["p1. alameda", "p2. alameda", "p3. alameda"]
names_unique = df_filtered['name'].unique()

dc = df_filtered.copy()
dc['date'] = pd.to_datetime(dc['date'], errors='coerce')
dc['date'] = dc['date'].dt.strftime('%d/%m/%y')
dc['message'] = dc['message'].astype(str).str.lower()
dc = dc[~dc['message'].str.contains('capilla', case=False, na=False)]
dc = dc[~dc['message'].str.contains('esquina', case=False, na=False)]
dc = dc[~dc['message'].str.contains('you deleted this message', case=False, na=False)]
dc = dc[~dc['message'].str.contains('fime', case=False, na=False)]

dc = dc.reset_index()
dc = dc.drop('index', axis=1)

vehiculo = ["m1", "m2", "m3", "ruta 601", "ruta 107", "didi", "carro", "ruta nuevo león san bernabé",
            "ruta nuevo león talleres","ruta 185 zertuche","ruta 185 20 nov","transmetro pablo livas"]
dc['vehicle'] = None
for index, row in dc.iterrows():
    for keyword in vehiculo:
        if keyword in str(row['message']).lower():
            dc.loc[index, 'vehicle'] = keyword
            break

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

dc['place'] = None
for index, row in dc.iterrows():
    for keyword in lugar:
        if keyword in str(row['message']).lower():
            if dc.loc[index, 'vehicle'] is None:
                if "detuvo" in str(row['message']).lower():
                    dc.loc[index, 'place'] = None
                    break
                else:
                    if keyword == "salí" or keyword == "sali":
                        dc.loc[index, 'place'] = "casa"
                        break
                    match keyword:
                        
                        case "p. alameda":
                            dc.loc[index, 'place'] = "p1. alameda"
                            break
                        case "p1":
                            dc.loc[index, 'place'] = "p1. alameda"
                            break
                        case "p2":
                            dc.loc[index, 'place'] = "p2. alameda"
                            break
                        case "p3":
                            dc.loc[index, 'place'] = "p3. alameda"
                            break
                        case "3.14159265 alameda":
                            dc.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.1416 alameda":
                            dc.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.141592 alameda":
                            dc.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.14 alameda":
                            dc.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "3.1415926535 alameda":
                            dc.loc[index, 'place'] = "3.1415 alameda"
                            break
                        case "cuauhtemoc":
                            dc.loc[index, 'place'] = "cuauhtémoc"
                            break
                    dc.loc[index, 'place'] = keyword
                    break

dc.to_excel('Emi.xlsx', index=False)
#import ordenar