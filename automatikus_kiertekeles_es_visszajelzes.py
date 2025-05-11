# -*- coding: utf-8 -*-
"""
@author: Szilágyi Dorka
"""
import os
import glob
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

#SEGÉDFÜGGVÉNYEK

#Neptun kódok kinyerése a fájlnévből
def neptun_kod_kinyerese(path):
    mappa = os.path.basename(path)
    m = re.search(r'([A-Za-z0-9]{6})', mappa)
    return m.group(1).upper() if m else None

#Mappák elérési útvonala
tanulo_mappa = r'C:\Users\Szilágyi Dorka\Desktop\Szakdolgozat\Kód2\train_fajlok\kibontott'
teszt_mappa = r'C:\Users\Szilágyi Dorka\Desktop\Szakdolgozat\Kód2\test_fajlok\kiertekeles'
megoldasok_mappa = r'C:\Users\Szilágyi Dorka\Desktop\Szakdolgozat\Submission_files\nepun_eredmenyek'

#Hibamértékek függvényei

def mape_szamolas(y_true, y_pred, eps=1e-8):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    return np.mean(np.abs((y_true - y_pred) / (y_true + eps))) * 100

def smape_szamolas(y_true, y_pred, eps=1e-8):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    num = np.abs(y_pred - y_true)
    den = (np.abs(y_true) + np.abs(y_pred)) / 2.0 + eps
    return np.mean(num/ den) * 100

def mase_szamolas(y_true, y_pred, y_train, m=1, eps=1e-8):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    y_train = np.array(y_train, dtype=float)
    #MAE(átlagos abszolút hiba) kiszámítása a modellre a tesztadatokon
    mae_model = np.mean(np.abs(y_true -y_pred))
    #A naiv modell átlagos hibájának kiszámolása a tanuló adaton 
    naiv_hiba = np.abs(y_train[m:] - y_train[:-m])
    skala = np.mean(naiv_hiba) + eps
    return mae_model / skala

#PDF függvény, amely elkészíti az eredményeket tartalmazó fájlt a visszajelzés céljából
def eredmenyek_df_exportalasa_pdf_formatumba (df, fajlnev='eredmenyek.pdf', cim='Hallgatói eredmények', disclaimer_szoveg='Eredmények közötti eltérések.'):
    
    num_rows, num_cols = df.shape
    
    fig_width = max(12, num_cols * 1.2)
    fig_height = max(8, num_rows * 0.5 + 1.5)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')
    ax.set_title(cim, fontsize=16, fontweight='bold', pad=20)
    
    table = ax.table(cellText=df.values,
                     colLabels=df.columns,
                     loc='center',
                     cellLoc ='center',
                     colColours=["#f2f2f2"] * num_cols)
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.1, 1.5)
    
    for i in range(num_cols):
        table.auto_set_column_width(col=i)
        
    fig.text(0.5, 0.02, disclaimer_szoveg,
             ha='center',fontsize=12, color='gray', style='italic')
    
    with PdfPages(fajlnev) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
       

#KIÉRTÉKELÉS

#Fájlnevek beolvasása
tanulo_fajlok = glob.glob(os.path.join(tanulo_mappa, '*.csv'))
teszt_fajlok = glob.glob(os.path.join(teszt_mappa, '*.csv'))
megoldas_fajlok = glob.glob(os.path.join(megoldasok_mappa, '*.csv'))

#Szótárak létrehozása a Neptun kódok szerinti fájlok összekapcsolásához
tanulo_szotar = {}
for f in tanulo_fajlok:
    kod = neptun_kod_kinyerese(f)
    if kod:
        tanulo_szotar[kod] = f
    else:
        print(f'Nem sikerült Neptun kódot kinyerni a {f} tanuló fájlból')
        
teszt_szotar = {}
for f in teszt_fajlok:
    kod = neptun_kod_kinyerese(f)
    if kod:
        teszt_szotar[kod] = f
    else:
        print(f'Nem sikerült Neptun kódot kinyerni a {f} teszt fájlból')
        
megoldas_szotar = {}
for f in megoldas_fajlok:
    kod = neptun_kod_kinyerese(f)
    if kod:
        megoldas_szotar[kod] = f
    else:
        print(f'Nem sikerült Neptun kódot kinyerni a {f} megoldás fájlból')

#Neptun kódok összetalálása
megegyezo_neptunok = set(tanulo_szotar) & set(teszt_szotar) & set(megoldas_szotar)
print(f'Összesen {len(megegyezo_neptunok)} Neptun kód található mindhárom mappában')


#A párosítások DataFrame-be való megjelenítése
sorok = []
for kod in sorted(megegyezo_neptunok):
    sorok.append({
        'Neptun': kod,
        'Tanuló fájl': tanulo_szotar[kod],
        'Teszt fájl': teszt_szotar[kod],
        'Megoldás fájl': megoldas_szotar[kod],
    })

csoportositas_df = pd.DataFrame(sorok)
print(csoportositas_df.to_string(index=False))

eredmenyek = []
for neptun in sorted(megegyezo_neptunok):
    tanulo_df = pd.read_csv(tanulo_szotar[neptun], parse_dates = ['SHOP_DATE'])
    teszt_df = pd.read_csv(teszt_szotar[neptun], parse_dates = ['SHOP_DATE'])
    megoldas_df = pd.read_csv(megoldas_szotar[neptun], parse_dates = ['SHOP_DATE'])
    
    y_train_q = tanulo_df['QUANTITY']
    y_test_q = teszt_df['QUANTITY']
    y_pred_q = megoldas_df['QUANTITY']
    
    y_train_s = tanulo_df['SPEND']
    y_test_s = teszt_df['SPEND']
    y_pred_s = megoldas_df['SPEND']
    
    #hibamértékek kiszámítása az előre definiált függvényekkel
    mape_q = round(mape_szamolas(y_test_q, y_pred_q), 2)
    smape_q = round(smape_szamolas(y_test_q, y_pred_q), 2)
    mase_q = round(mase_szamolas(y_test_q, y_pred_q, y_train_q), 2)
    
    mape_s = round(mape_szamolas(y_test_s, y_pred_s), 2)
    smape_s = round(smape_szamolas(y_test_s, y_pred_s), 2)
    mase_s = round(mase_szamolas(y_test_s, y_pred_s, y_train_s), 2)
    
    eredmenyek.append({
        'Neptun': neptun,
        'MAPE_QUANTITY': mape_q,
        'sMAPE_QUANTITY': smape_q,
        'MASE_QUANTITY': mase_q,
        'MAPE_SPEND': mape_s,
        'sMAPE_SPEND': smape_s,
        'MASE_SPEND': mase_s
    })
    
eredmények_df = pd.DataFrame(eredmenyek)

#Átlagok kiszámítása minden metrikára:
eredmények_df['MAPE_ÁTLAG'] = round((eredmények_df['MAPE_QUANTITY'] + eredmények_df['MAPE_SPEND']) / 2, 2)
eredmények_df['sMAPE_ÁTLAG'] = round((eredmények_df['sMAPE_QUANTITY'] + eredmények_df['sMAPE_SPEND']) / 2, 2)
eredmények_df['MASE_ÁTLAG'] = round((eredmények_df['MASE_QUANTITY'] + eredmények_df['MASE_SPEND']) / 2, 2)

#A három átlag szerinti rangsor
metrikak = ['MAPE_ÁTLAG', 'sMAPE_ÁTLAG', 'MASE_ÁTLAG']
for m in metrikak:
    eredmények_df[f'rangsor_{m}'] = eredmények_df[m].rank(method='min', ascending =True)
    
#Átlagolt rangsor egyszerű átlaggal számolva
rangsor = [f'rangsor_{m}' for m in metrikak]
eredmények_df['átlag_rangsor'] = eredmények_df[rangsor].mean(axis=1)
eredmények_df['átlag_rangsor'] = eredmények_df['átlag_rangsor'].round(2)

#Végleges sorrend az átlag_rangsor alapján
eredmények_df = eredmények_df.sort_values('átlag_rangsor').reset_index(drop=True)
eredmények_df['Végleges_Rangsor'] = eredmények_df.index + 1


#Az eredményeket tartalmazó PDF elkészítése  
eredmenyek_df_exportalasa_pdf_formatumba(
    eredmények_df,
    fajlnev='eredmenyek.pdf',
    disclaimer_szoveg='*Figyelem: A rangsor kizárólag a beadott eredményeken alapul, és nem veszi figyelembe az esetleges eltéréseket a feladatok nehézségi szintje között. A kevésbé jó helyezések a rangsorban esetenként abból is adódhatnak, hogy egyes hallgatók nehezebb bemeneti adatkészletet kaptak.')