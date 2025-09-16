import pandas as pd
import re
import openpyxl
import datetime
import numpy as np

data=pd.read_excel("data.xlsx",sheet_name="Sheet1")
names=data['name'].unique()
for name in names:
    book=openpyxl.Workbook()
    hoja=book.active
    book.save(f"{name}.xlsx")
    dataCar=data[data['name']==name]
    dataCar.to_excel(f"{name}.xlsx",index=False)
    print(f"{name}.xlsx guardado")

for name in names:
    book = pd.read_excel(f"{name}.xlsx")
    df = pd.DataFrame()
    date = []#
    time_start = []#
    time_end = []#
    place_start = []#
    place_end = []#
    duration = []#
    vehicle = []#
    note = []#
    viaje=0
    cambio_tiempo = True
    cambio_lugar = True
    tamaño_i = 0
    tamaño_f = 0
    i=0
    notas = []
    while i < len(book):
        fecha = not pd.isna(book.iloc[i,0])
        hora = not pd.isna(book.iloc[i,3])
        marca = not pd.isna(book.iloc[i,4])
        vehiculo = not pd.isna(book.iloc[i,5])
        lugar = not pd.isna(book.iloc[i,6])
        if not(lugar or vehiculo):
            notas.append(book.iloc[i,2])
        else:
            
            if lugar and cambio_tiempo:
                
                try:
                    h,m,c=map(int,book.iloc[i,3].split(':'))
                    start_time = (h*3600)+(m*60)+c
                    time_start.append(str(book.iloc[i,4]))
                    place_start.append(book.iloc[i,6])
                    date.append(book.iloc[i,0])
                    cambio_tiempo = False
                except:
                    notas.append(book.iloc[i,2])
                
            elif lugar and not cambio_tiempo:
                try:    
                    h,m,c=map(int,book.iloc[i,3].split(':'))
                    end_time = (h*3600)+(m*60)+c
                    tamaño_i = len(place_start)
                    tamaño_f = len(place_end)+1
                    if tamaño_i < tamaño_f:
                        place_start.append(place_end[-1])
                    place_end.append(book.iloc[i,6])
                    time_end.append(str(book.iloc[i,4]))
                    
                    if start_time > end_time:
                        start_time += 3600*12
                    result = end_time - start_time 
                    h=result//3600
                    m=(result%3600)//60
                    c=result%60

                    duration.append(f"{h:02d}:{m:02d}:{c:02d}")
                    if len(notas)==0:
                        note.append("sin comentarios")
                    else:
                        note.append(notas)
                    if len(vehicle)<len(time_end):
                        vehicle.append("caminando")
                    if place_start[-1] == place_end[-1]:
                        date.pop(-1)
                        time_start.pop(-1)
                        time_end.pop(-1)
                        duration.pop(-1)
                        place_start.pop(-1)
                        place_end.pop(-1)
                        vehicle.pop(-1)
                        note.pop(-1)
                    if result < 0:
                        date.pop(-1)
                        time_start.pop(-1)
                        time_end.pop(-1)
                        duration.pop(-1)
                        place_start.pop(-1)
                        place_end.pop(-1)
                        vehicle.pop(-1)
                        note.pop(-1)
                    cambio_tiempo = True
                    cambio_lugar = True
                    
                    notas = []
                    continue
                except:
                    notas.append(book.iloc[i,2])
            if vehiculo and cambio_lugar:
                try:
                    h,m,c=map(int,book.iloc[i,3].split(':'))
                    start_time = (h*3600)+(m*60)+c
                    vehicle.append(book.iloc[i,5])
                    time_start.pop(-1)
                    time_start.append(book.iloc[i,4])
                    cambio_lugar = False
                except:
                    notas.append(book.iloc[i,2])
        i+=1
    date.pop(-1)
    time_start.pop(-1)
    place_start.pop(-1)
    df["date"] = date
    df["time_start"] = time_start
    df["time_end"] = time_end
    df["place_start"] = place_start
    df["place_end"] = place_end
    df["duration"] = duration
    df["vehicle"] = vehicle
    df["note"] = note
    df.to_excel(f"{name}.xlsx",index=False)
    print(f"{name}.xlsx guardado")
                