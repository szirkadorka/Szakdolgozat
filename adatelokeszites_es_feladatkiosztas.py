# -*- coding: utf-8 -*-
"""
@author: Szilágyi Dorka
"""

import os
import pandas as pd
import random
import zipfile
import string 

#SEGÉDFÜGGVÉNYEK

#Neptun kód generálása véletlenszerű karakterekből és számokból

def neptun_kod_generator():
    elso_karakter = random.choice(string.ascii_uppercase) 
    tobbi_karakter = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return elso_karakter + tobbi_karakter

#A Neptun kódok létrehozása és mentése Excel fájlba

neptun_kodok = [neptun_kod_generator() for i in range(25)]
neptun_df = pd.DataFrame(neptun_kodok, columns=['NEPTUN'])
neptun_fajl = 'neptun_kodok.xlsx'
neptun_df.to_excel(neptun_fajl, index=False)

#Könyvtár létrehozása a kiértékeléshez szükséges teszt fájlok tárolására
kiertekeles_konyvtar = 'kiertekeles'
if not os.path.exists(kiertekeles_konyvtar):
    os.makedirs(kiertekeles_konyvtar)

#FELADATOK ELŐKÉSZÍTÉSE

#A könyvtár, ahol a bemeneti fájlok találhatóak
konyvtar = r'C:\Users\Szilágyi Dorka\Desktop\Szakdolgozat\Kód\transactions_subset'

#Dátum oszlop mentése egy váltotóba, hogy a megfelelő formára alakítás elvégezhető legyen
datum_oszlop = 'SHOP_DATE'

#Az összes CSV fájlt összefűzzük 
teljes_adat = []
for fajlnev in os.listdir(konyvtar):
    if fajlnev.endswith('.csv'):
        fajlutvonal = os.path.join(konyvtar, fajlnev)
        df = pd.read_csv(fajlutvonal)
        
        #SHOP_DATE oszlop dátummá konvertálása
        if datum_oszlop in df.columns: 
            df[datum_oszlop] = pd.to_datetime(df[datum_oszlop], format= '%Y%m%d').dt.date
            
        #QUANTITY és SPEND összesítése SHOP_DATE és PROD_CODE szerinti csoportosítással
        osszegzes_df = df.groupby(['SHOP_DATE', 'PROD_CODE']).agg({
            'QUANTITY': 'sum',
            'SPEND': 'sum'
        }).reset_index()
        
        teljes_adat.append(osszegzes_df)
            
#Az összesített adatok egy DataFrame-be fűzése
teljes_df = pd.concat(teljes_adat, ignore_index=True)

#Minden termékkódnál megszámolja a kód a leghosszabb, megszakítás nélküli napi vásárlási szakaszt
termekkod_lista = []
for termekkod, csoport in teljes_df.groupby('PROD_CODE'):
    csoport = csoport.sort_values(by='SHOP_DATE')
    datumok = pd.to_datetime(csoport['SHOP_DATE']).drop_duplicates()
    kulonbsegek = (datumok -datumok.shift()).dt.days
    leghosszabb = (kulonbsegek == 1).astype(int).groupby(kulonbsegek.ne(1).cumsum()).cumsum().max()
    if leghosszabb >= 800:
        termekkod_lista.append(termekkod)
        
#Szűrés az alapján, hogy csak olyan termékkódot lehessen kiosztani, aminek van minimum 800 napból álló megszakítás nélküli vásárlási szakasza   
hasznalhato_df = teljes_df[teljes_df['PROD_CODE'].isin(termekkod_lista)].copy()  
egyedi_hasznalhato_termekkodok = list(hasznalhato_df['PROD_CODE'].unique())

min_napok_szama = hasznalhato_df.groupby('PROD_CODE').size().min()

#FELADATOK KIADÁSA

#Neptun kódok betöltése
neptun_df = pd.read_excel(neptun_fajl)
neptun_kodok = neptun_df['NEPTUN'].tolist()

#Minden Neptun kódhoz egy termékkód hozzárendelése
for i, neptun_kod in enumerate(neptun_kodok):
    random_termekkod = random.choice(egyedi_hasznalhato_termekkodok)
    egyedi_hasznalhato_termekkodok.remove(random_termekkod)
    szurt_df = hasznalhato_df[hasznalhato_df['PROD_CODE'] == random_termekkod]
    szurt_df = szurt_df.sort_values(by=datum_oszlop)
    
    #Minden Neptun kódhoz a minimális napok számának kiválasztása, hogy azonos hosszúsági legyen minden feladat
    szurt_df = szurt_df.iloc[:min_napok_szama]
    
    #Az idősorok 80-20%-os szétosztása a tanuló és teszt adatokra
    tanulo_halmaz = int(len(szurt_df) * 0.8)
    tanulo_df = szurt_df.iloc[:tanulo_halmaz]
    teszt_df = szurt_df.iloc[tanulo_halmaz:]
    
    #CSV fájl létrehozása a tanuló adatokhoz
    feladat_tanulo = f'{neptun_kod}_tanulo_{i + 1}.csv'
    tanulo_df.to_csv(feladat_tanulo, index=False)
    
    #CSV fájl létrehozása a teszt adatokhoz és a létrehozott könyvtárba való mentés
    feladat_teszt = f'{neptun_kod}_teszt_{i + 1}.csv'
    teszt_df.to_csv(os.path.join(kiertekeles_konyvtar, feladat_teszt), index=False)
    
    #ZIP fájl létrehozása és a tanuló adatfájl hozzáadása
    zip_fajl = f'{neptun_kod}_feladat.zip'
    with zipfile.ZipFile(zip_fajl, 'w') as zipf:
        zipf.write(feladat_tanulo)
     
    #A tanuló adatfájl törlése, hogy csak a ZIP-ben maradjon meg, ne legyen feleslegesen kétszeresen tárolva
    os.remove(feladat_tanulo)
 
print('Minden elkészült!')