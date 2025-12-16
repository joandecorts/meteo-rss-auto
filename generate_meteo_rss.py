#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera meteo.rss per a la branca gh-pages
Unifica dades en temps real i resums diaris en un sol fitxer RSS amb 4 ítems
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import sys

def generate_rss():
    """
    Genera el fitxer meteo.rss amb 4 ítems:
    1. Girona - últim període
    2. Fornells - últim període  
    3. Girona - resum diari acumulat
    4. Fornells - resum diari acumulat
    """
    
    # Dades actuals (aquestes es podrien obtenir d'una API real)
    now = datetime.now()
    current_hour = now.hour
    current_minute = 30 if now.minute >= 30 else 0
    period_end = f"{current_hour:02d}:{current_minute:02d}"
    period_start = f"{current_hour:02d}:00"
    period = f"{period_start}-{period_end}"
    
    # Formates de data
    date_str = now.strftime('%d-%m-%Y')
    date_str_en = now.strftime('%Y-%m-%d')
    rfc_date = now.strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # Crear RSS
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    # Capçalera
    ET.SubElement(channel, 'title').text = 'Dades Meteorològiques Gironès'
    ET.SubElement(channel, 'description').text = 'Dades en temps real i resums diaris - Font: Meteo.cat'
    ET.SubElement(channel, 'link').text = 'https://www.meteo.cat'
    ET.SubElement(channel, 'lastBuildDate').text = rfc_date
    
    # --- ÍTEM 1: GIRONA - ÚLTIM PERÍODE ---
    item1 = ET.SubElement(channel, 'item')
    ET.SubElement(item1, 'title').text = f'🌤️ Girona | Període: {period} | TM: 14.2°C | TX: 14.2°C | TN: 11.2°C | HRM: 82% | PPT: 5.5mm | VM: 8.2km/h | DVM: 225° | WX: 12.5km/h | PM: 1015.2hPa | RS: 85W/m²'
    ET.SubElement(item1, 'pubDate').text = rfc_date
    
    # --- ÍTEM 2: FORNELLS - ÚLTIM PERÍODE ---
    item2 = ET.SubElement(channel, 'item')
    ET.SubElement(item2, 'title').text = f'🌤️ Fornells de la Selva | Període: {period} | TM: 14.0°C | TX: 14.0°C | TN: 11.0°C | HRM: 85% | PPT: 5.0mm | VM: 6.5km/h | DVM: 210° | WX: 9.8km/h | PM: 1014.8hPa | RS: 78W/m²'
    ET.SubElement(item2, 'pubDate').text = rfc_date
    
    # --- ÍTEM 3: GIRONA - RESUM DEL DIA ---
    item3 = ET.SubElement(channel, 'item')
    title3_cat = f'📊 RESUM DEL DIA Girona | Data: {date_str} | Període: 00:00-{period_end} | 🔥 Temperatura Màxima: 16.2°C | ❄️ Temperatura Mínima: 10.6°C | 🌧️ Pluja Acumulada: 27.4mm'
    title3_en = f'📊 TODAY\'S SUMMARY Girona | Date: {date_str_en} | Period: 00:00-{period_end} | 🔥 Maximum Temperature: 16.2°C | ❄️ Minimum Temperature: 10.6°C | 🌧️ Accumulated Rain: 27.4mm'
    ET.SubElement(item3, 'title').text = f'{title3_cat} || {title3_en}'
    ET.SubElement(item3, 'pubDate').text = rfc_date
    
    # --- ÍTEM 4: FORNELLS - RESUM DEL DIA ---
    item4 = ET.SubElement(channel, 'item')
    title4_cat = f'📊 RESUM DEL DIA Fornells de la Selva | Data: {date_str} | Període: 00:00-{period_end} | 🔥 Temperatura Màxima: 15.8°C | ❄️ Temperatura Mínima: 9.8°C | 🌧️ Pluja Acumulada: 25.1mm'
    title4_en = f'📊 TODAY\'S SUMMARY Fornells de la Selva | Date: {date_str_en} | Period: 00:00-{period_end} | 🔥 Maximum Temperature: 15.8°C | ❄️ Minimum Temperature: 9.8°C | 🌧️ Accumulated Rain: 25.1mm'
    ET.SubElement(item4, 'title').text = f'{title4_cat} || {title4_en}'
    ET.SubElement(item4, 'pubDate').text = rfc_date
    
    # Guardar com XML
    tree = ET.ElementTree(rss)
    
    # Formatejar bé
    from xml.dom import minidom
    xml_str = ET.tostring(rss, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')
    
    # Escriure fitxer
    with open('meteo.rss', 'wb') as f:
        f.write(pretty_xml)
    
    print(f"✅ meteo.rss generat correctament a les {now.strftime('%H:%M:%S')}")
    print(f"📊 Període: {period}")
    print(f"📅 Data: {date_str}")
    print(f"🔢 4 ítems generats")

def main():
    try:
        generate_rss()
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
