import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import re
import sys
import os

def safe_float(value, default=0.0):
    """Convierte seguridad un valor a float"""
    if value is None or value == '':
        return default
        
    value_str = str(value).strip()
    
    # Manejar "(s/d)" - Sin Datos
    if '(s/d)' in value_str or value_str == 's/d' or value_str == 'N/A':
        return default
    
    # Extraer números
    match = re.search(r'([-]?\d+\.?\d*)', value_str.replace(',', '.'))
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            return default
    
    return default

def get_meteo_data():
    try:
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar la tabla por la clase 'tblperiode'
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            return None
            
        rows = table.find_all('tr')
        if len(rows) < 2:
            return None
        
        # La segunda fila contiene los datos más recientes
        data_row = rows[1]
        cells = data_row.find_all('td')
        
        if len(cells) < 9:
            return None
        
        # Extraer datos
        hora = cells[0].text.strip()
        temp = safe_float(cells[1].text)
        max_temp = safe_float(cells[2].text)
        min_temp = safe_float(cells[3].text)
        hum = safe_float(cells[4].text)
        wind = safe_float(cells[5].text)
        gust = safe_float(cells[6].text)
        precip = safe_float(cells[7].text)
        pressure = safe_float(cells[8].text)
        
        return {
            'hora': hora,
            'temp': temp,
            'max_temp': max_temp,
            'min_temp': min_temp,
            'hum': hum,
            'wind': wind,
            'gust': gust,
            'precip': precip,
            'pressure': pressure
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_rss():
    data = get_meteo_data()
    
    # Obtener timestamp actual
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    timestamp = int(now.timestamp())
    
    # Si no hay datos, usar valores por defecto
    if not data:
        data = {
            'hora': 'Última hora',
            'temp': 0.0,
            'max_temp': 0.0,
            'min_temp': 0.0,
            'hum': 0.0,
            'wind': 0.0,
            'gust': 0.0,
            'precip': 0.0,
            'pressure': 0.0
        }
    
    # 🎯 FORMATO SUPER SIMPLE CON [CAT] y [GB]
    title = (
        f"[CAT] {data['hora']} | "
        f"Temp:{data['temp']}°C | "
        f"Màx:{data['max_temp']}°C | "
        f"Mín:{data['min_temp']}°C | "
        f"Hum:{data['hum']}% | "
        f"Vent:{data['wind']}km/h | "
        f"Ràfegues:{data['gust']}km/h | "
        f"Precip:{data['precip']}mm | "
        f"Pressió:{data['pressure']}hPa | "
        f"[GB] {data['hora']} | "
        f"Temp:{data['temp']}°C | "
        f"Max:{data['max_temp']}°C | "
        f"Min:{data['min_temp']}°C | "
        f"Hum:{data['hum']}% | "
        f"Wind:{data['wind']}km/h | "
        f"Gusts:{data['gust']}km/h | "
        f"Precip:{data['precip']}mm | "
        f"Pressure:{data['pressure']}hPa"
    )
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat RSS</title>
  <link>https://www.meteo.cat</link>
  <description>Automated meteorological data - Dades meteorològiques automàtiques</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{title}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    # Guardar archivo RSS
    with open('meteo.rss', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    return True

if __name__ == "__main__":
    success = generate_rss()
    sys.exit(0)
