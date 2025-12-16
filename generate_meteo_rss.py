#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per generar meteo.rss amb dades acumulades del dia
Calcula: TX màxima, TN mínima, PPT acumulada de tots els períodes del dia
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
import json
import time
import sys
import os
from collections import defaultdict

# Configuració
METEO_API_BASE = "https://api.meteo.cat"
OUTPUT_FILE = "meteo.rss"

def get_all_periods_today():
    """
    Obtenir totes les dades dels períodes del dia actual (des de 00:00)
    Retorna: diccionari amb TX, TN, PPT de cada període per a cada estació
    """
    print("📅 Obtenint totes les dades del dia actual...")
    
    today = datetime.now().date()
    
    # AQUÍ CAL IMPLEMENTAR LA CONNEXIÓ A L'API DE METEO.CAT
    # Suposem que tenim una funció que retorna totes les dades del dia
    
    # Dades simulades d'exemple - EN LA REALITAT AIXÒ S'HANDRIA D'OBTENIR DE L'API
    # Cada llista conté dades de cada període del dia: [TX, TN, PPT]
    
    simulated_data = {
        "Girona": [
            # Període, TX, TN, PPT
            ["00:00-00:30", 8.5, 7.2, 0.0],
            ["00:30-01:00", 8.3, 7.0, 0.0],
            ["01:00-01:30", 8.0, 6.8, 0.0],
            ["01:30-02:00", 7.8, 6.5, 0.0],
            ["02:00-02:30", 7.5, 6.2, 0.0],
            ["02:30-03:00", 7.2, 6.0, 0.0],
            ["03:00-03:30", 7.0, 5.8, 0.0],
            ["03:30-04:00", 6.8, 5.5, 0.0],
            ["04:00-04:30", 6.5, 5.2, 0.0],
            ["04:30-05:00", 6.3, 5.0, 0.0],
            ["05:00-05:30", 6.2, 4.8, 0.0],
            ["05:30-06:00", 6.0, 4.6, 0.0],
            ["06:00-06:30", 6.2, 4.8, 0.0],
            ["06:30-07:00", 6.5, 5.0, 0.0],
            ["07:00-07:30", 7.0, 5.5, 0.0],
            ["07:30-08:00", 8.0, 6.2, 0.0],
            ["08:00-08:30", 9.5, 7.5, 0.0],
            ["08:30-09:00", 11.0, 8.8, 0.0],
            ["09:00-09:30", 12.5, 10.0, 0.0],
            ["09:30-10:00", 13.8, 11.0, 0.0],
            ["10:00-10:30", 14.5, 11.5, 0.0],
            ["10:30-11:00", 15.0, 12.0, 0.0],
            ["11:00-11:30", 15.3, 12.2, 0.0],
            ["11:30-12:00", 15.5, 12.5, 0.2],
            ["12:00-12:30", 15.8, 12.8, 0.5],
            ["12:30-13:00", 16.0, 13.0, 1.2],
            ["13:00-13:30", 16.2, 13.2, 2.0],
            ["13:30-14:00", 16.0, 13.0, 2.5],
            ["14:00-14:30", 15.8, 12.8, 3.0],
            ["14:30-15:00", 15.5, 12.5, 3.2],
            ["15:00-15:30", 15.2, 12.2, 3.5],
            ["15:30-16:00", 15.0, 12.0, 4.0],
            ["16:00-16:30", 14.8, 11.8, 4.5],
            ["16:30-17:00", 14.5, 11.5, 5.0],
            ["17:00-17:30", 14.2, 11.2, 5.5],  # Últim període
        ],
        "Fornells de la Selva": [
            ["00:00-00:30", 8.2, 6.8, 0.0],
            ["00:30-01:00", 8.0, 6.5, 0.0],
            ["01:00-01:30", 7.8, 6.2, 0.0],
            ["01:30-02:00", 7.5, 6.0, 0.0],
            ["02:00-02:30", 7.2, 5.8, 0.0],
            ["02:30-03:00", 7.0, 5.5, 0.0],
            ["03:00-03:30", 6.8, 5.2, 0.0],
            ["03:30-04:00", 6.5, 5.0, 0.0],
            ["04:00-04:30", 6.2, 4.8, 0.0],
            ["04:30-05:00", 6.0, 4.6, 0.0],
            ["05:00-05:30", 5.8, 4.4, 0.0],
            ["05:30-06:00", 5.6, 4.2, 0.0],
            ["06:00-06:30", 5.8, 4.4, 0.0],
            ["06:30-07:00", 6.0, 4.6, 0.0],
            ["07:00-07:30", 6.5, 5.0, 0.0],
            ["07:30-08:00", 7.5, 5.8, 0.0],
            ["08:00-08:30", 9.0, 7.0, 0.0],
            ["08:30-09:00", 10.5, 8.2, 0.0],
            ["09:00-09:30", 12.0, 9.5, 0.0],
            ["09:30-10:00", 13.2, 10.5, 0.0],
            ["10:00-10:30", 14.0, 11.2, 0.0],
            ["10:30-11:00", 14.5, 11.8, 0.0],
            ["11:00-11:30", 14.8, 12.0, 0.0],
            ["11:30-12:00", 15.0, 12.2, 0.1],
            ["12:00-12:30", 15.2, 12.5, 0.3],
            ["12:30-13:00", 15.5, 12.8, 0.8],
            ["13:00-13:30", 15.8, 13.0, 1.5],
            ["13:30-14:00", 15.7, 12.8, 2.0],
            ["14:00-14:30", 15.5, 12.5, 2.5],
            ["14:30-15:00", 15.2, 12.2, 2.8],
            ["15:00-15:30", 15.0, 12.0, 3.2],
            ["15:30-16:00", 14.8, 11.8, 3.5],
            ["16:00-16:30", 14.5, 11.5, 4.0],
            ["16:30-17:00", 14.2, 11.2, 4.5],
            ["17:00-17:30", 14.0, 11.0, 5.0],  # Últim període
        ]
    }
    
    return simulated_data

def calculate_daily_accumulated(all_data):
    """
    Calcular acumulats del dia a partir de totes les dades
    Retorna: diccionari amb TX_diaria, TN_diaria, PPT_acumulada, last_period
    """
    print("🧮 Calculant acumulats del dia...")
    
    results = {}
    
    for city, periods in all_data.items():
        if not periods:
            print(f"⚠️  No hi ha dades per a {city}")
            continue
        
        # Inicialitzar amb el primer període
        first_tx = periods[0][1] if periods[0][1] is not None else -999
        first_tn = periods[0][2] if periods[0][2] is not None else 999
        first_ppt = periods[0][3] if periods[0][3] is not None else 0
        
        tx_daily = first_tx
        tn_daily = first_tn
        ppt_acumulada = first_ppt
        
        # Recórrer tots els períodes (començant pel segon)
        for period_data in periods[1:]:
            period_str, tx, tn, ppt = period_data
            
            # Actualitzar màxima
            if tx is not None and tx > tx_daily:
                tx_daily = tx
            
            # Actualitzar mínima
            if tn is not None and tn < tn_daily:
                tn_daily = tn
            
            # Acumular pluja
            if ppt is not None:
                ppt_acumulada += ppt
        
        # Obtenir l'últim període
        last_period_str = periods[-1][0] if periods else "00:00-00:00"
        
        results[city] = {
            "tx_daily": round(tx_daily, 1),
            "tn_daily": round(tn_daily, 1),
            "ppt_acumulada": round(ppt_acumulada, 1),
            "last_period_end": last_period_str.split("-")[1]  # Agafar la hora final
        }
        
        print(f"  📍 {city}: TX={tx_daily:.1f}°C, TN={tn_daily:.1f}°C, PPT={ppt_acumulada:.1f}mm")
    
    return results

def get_current_period_data():
    """
    Obtenir dades de l'últim període (ítems 1 i 2)
    """
    print("🌤️  Obtenint dades de l'últim període...")
    
    now = datetime.now()
    hour = now.hour
    minute = 30 if now.minute >= 30 else 0
    
    # Format del període
    period_start = f"{hour:02d}:00"
    period_end = f"{hour:02d}:{minute:02d}"
    period_str = f"{period_start}-{period_end}"
    
    # Dades de l'últim període (simulades - substituir amb API real)
    current_data = {
        "Girona": {
            "period": period_str,
            "TM": 14.2,
            "TX": 14.2,
            "TN": 11.2,
            "HRM": 82,
            "PPT": 5.5,
            "VM": 8.2,
            "DVM": 225,
            "WX": 12.5,
            "PM": 1015.2,
            "RS": 85,
        },
        "Fornells de la Selva": {
            "period": period_str,
            "TM": 14.0,
            "TX": 14.0,
            "TN": 11.0,
            "HRM": 85,
            "PPT": 5.0,
            "VM": 6.5,
            "DVM": 210,
            "WX": 9.8,
            "PM": 1014.8,
            "RS": 78,
        }
    }
    
    return current_data

def generate_rss():
    """
    Funció principal que genera el fitxer RSS complet
    """
    print("\n" + "="*60)
    print("🚀 GENERANT METEO.RSS AMB DADES ACUMULADES DEL DIA")
    print("="*60)
    
    # 1. Obtenir totes les dades del dia per als càlculs acumulatius
    all_daily_data = get_all_periods_today()
    
    # 2. Calcular acumulats del dia (TX diària, TN diària, PPT acumulada)
    daily_accumulated = calculate_daily_accumulated(all_daily_data)
    
    # 3. Obtenir dades de l'últim període (per als ítems 1 i 2)
    current_data = get_current_period_data()
    
    # 4. Preparar dates
    now = datetime.now()
    date_str = now.strftime('%d-%m-%Y')
    date_str_en = now.strftime('%Y-%m-%d')
    rfc_date = now.strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # 5. Crear RSS
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    # Capçalera
    ET.SubElement(channel, 'title').text = 'Dades Meteorològiques Gironès'
    ET.SubElement(channel, 'description').text = 'Dades en temps real i resums diaris acumulatius - Font: Meteo.cat'
    ET.SubElement(channel, 'link').text = 'https://www.meteo.cat'
    ET.SubElement(channel, 'lastBuildDate').text = rfc_date
    
    print("\n📝 GENERANT ELS 4 ÍTEMS RSS:")
    print("-"*40)
    
    # --- ÍTEM 1: GIRONA - ÚLTIM PERÍODE ---
    g = current_data["Girona"]
    title1 = f"🌤️ Girona | Període: {g['period']} | TM: {g['TM']}°C | TX: {g['TX']}°C | TN: {g['TN']}°C | HRM: {g['HRM']}% | PPT: {g['PPT']}mm | VM: {g['VM']}km/h | DVM: {g['DVM']}° | WX: {g['WX']}km/h | PM: {g['PM']}hPa | RS: {g['RS']}W/m²"
    item1 = ET.SubElement(channel, 'item')
    ET.SubElement(item1, 'title').text = title1
    ET.SubElement(item1, 'pubDate').text = rfc_date
    print("✅ Ítem 1: Girona (últim període)")
    
    # --- ÍTEM 2: FORNELLS - ÚLTIM PERÍODE ---
    f = current_data["Fornells de la Selva"]
    title2 = f"🌤️ Fornells de la Selva | Període: {f['period']} | TM: {f['TM']}°C | TX: {f['TX']}°C | TN: {f['TN']}°C | HRM: {f['HRM']}% | PPT: {f['PPT']}mm | VM: {f['VM']}km/h | DVM: {f['DVM']}° | WX: {f['WX']}km/h | PM: {f['PM']}hPa | RS: {f['RS']}W/m²"
    item2 = ET.SubElement(channel, 'item')
    ET.SubElement(item2, 'title').text = title2
    ET.SubElement(item2, 'pubDate').text = rfc_date
    print("✅ Ítem 2: Fornells de la Selva (últim període)")
    
    # --- ÍTEM 3: GIRONA - RESUM DEL DIA (ACUMULAT) ---
    g_acc = daily_accumulated.get("Girona", {})
    period_end = g_acc.get("last_period_end", "17:30")
    period_str = f"00:00-{period_end}"
    
    title3_cat = f"📊 RESUM DEL DIA Girona | Data: {date_str} | Període: {period_str} | 🔥 Temperatura Màxima: {g_acc.get('tx_daily', 0.0)}°C | ❄️ Temperatura Mínima: {g_acc.get('tn_daily', 0.0)}°C | 🌧️ Pluja Acumulada: {g_acc.get('ppt_acumulada', 0.0)}mm"
    title3_en = f"📊 TODAY'S SUMMARY Girona | Date: {date_str_en} | Period: {period_str} | 🔥 Maximum Temperature: {g_acc.get('tx_daily', 0.0)}°C | ❄️ Minimum Temperature: {g_acc.get('tn_daily', 0.0)}°C | 🌧️ Accumulated Rain: {g_acc.get('ppt_acumulada', 0.0)}mm"
    title3 = f"{title3_cat} || {title3_en}"
    
    item3 = ET.SubElement(channel, 'item')
    ET.SubElement(item3, 'title').text = title3
    ET.SubElement(item3, 'pubDate').text = rfc_date
    print("✅ Ítem 3: Girona (resum diari acumulat)")
    print(f"   → Càlculs: TX={g_acc.get('tx_daily')}°C (màxima), TN={g_acc.get('tn_daily')}°C (mínima), PPT={g_acc.get('ppt_acumulada')}mm (suma)")
    
    # --- ÍTEM 4: FORNELLS - RESUM DEL DIA (ACUMULAT) ---
    f_acc = daily_accumulated.get("Fornells de la Selva", {})
    period_end = f_acc.get("last_period_end", "17:30")
    period_str = f"00:00-{period_end}"
    
    title4_cat = f"📊 RESUM DEL DIA Fornells de la Selva | Data: {date_str} | Període: {period_str} | 🔥 Temperatura Màxima: {f_acc.get('tx_daily', 0.0)}°C | ❄️ Temperatura Mínima: {f_acc.get('tn_daily', 0.0)}°C | 🌧️ Pluja Acumulada: {f_acc.get('ppt_acumulada', 0.0)}mm"
    title4_en = f"📊 TODAY'S SUMMARY Fornells de la Selva | Date: {date_str_en} | Period: {period_str} | 🔥 Maximum Temperature: {f_acc.get('tx_daily', 0.0)}°C | ❄️ Minimum Temperature: {f_acc.get('tn_daily', 0.0)}°C | 🌧️ Accumulated Rain: {f_acc.get('ppt_acumulada', 0.0)}mm"
    title4 = f"{title4_cat} || {title4_en}"
    
    item4 = ET.SubElement(channel, 'item')
    ET.SubElement(item4, 'title').text = title4
    ET.SubElement(item4, 'pubDate').text = rfc_date
    print("✅ Ítem 4: Fornells de la Selva (resum diari acumulat)")
    print(f"   → Càlculs: TX={f_acc.get('tx_daily')}°C (màxima), TN={f_acc.get('tn_daily')}°C (mínima), PPT={f_acc.get('ppt_acumulada')}mm (suma)")
    
    # 6. Guardar XML
    tree = ET.ElementTree(rss)
    
    # Format boníc
    from xml.dom import minidom
    xml_str = ET.tostring(rss, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')
    
    # Escriure fitxer
    with open(OUTPUT_FILE, 'wb') as f:
        f.write(pretty_xml)
    
    # 7. Mostrar resum
    print("\n" + "="*60)
    print(f"🎉 FITXER '{OUTPUT_FILE}' GENERAT CORRECTAMENT!")
    print("="*60)
    
    print(f"\n📊 RESUM FINAL DEL DIA {date_str}:")
    print("-"*40)
    
    for city in ["Girona", "Fornells de la Selva"]:
        acc = daily_accumulated.get(city, {})
        print(f"\n📍 {city}:")
        print(f"   • Temperatura Màxima del dia: {acc.get('tx_daily', 0.0)}°C")
        print(f"   • Temperatura Mínima del dia: {acc.get('tn_daily', 0.0)}°C")
        print(f"   • Pluja Acumulada del dia: {acc.get('ppt_acumulada', 0.0)}mm")
        print(f"   • Període: 00:00-{acc.get('last_period_end', '--:--')}")
    
    print(f"\n⏰ Hora de generació: {now.strftime('%H:%M:%S')}")
    print(f"📏 Mida del fitxer: {len(pretty_xml) // 1024} KB")
    
    # Mostrar mostra del contingut
    print("\n📋 MOSTRA DEL RSS GENERAT:")
    print("-"*40)
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:30]):  # Primeres 30 línies
            print(f"{i+1:3d}: {line.rstrip()}")
        if len(lines) > 30:
            print("... (més línies)")

def main():
    """Punt d'entrada principal"""
    try:
        generate_rss()
        return 0
    except Exception as e:
        print(f"\n❌ ERROR CRÍTIC: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
