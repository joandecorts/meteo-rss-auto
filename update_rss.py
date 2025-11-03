import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import re

def safe_float(value, default=0.0):
    """
    Convierte seguridad un valor a float, manejando (s/d) y otros casos
    """
    if value is None:
        return default
        
    value_str = str(value).strip()
    
    # Manejar "(s/d)" - Sin Datos
    if '(s/d)' in value_str or value_str == 's/d':
        return default
    
    # Manejar valores vacíos
    if not value_str or value_str == '':
        return default
    
    # Extraer números de cadenas como "21.2°C"
    match = re.search(r'([-]?\d+\.?\d*)', value_str)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            return default
    
    return default

def get_meteo_data():
    try:
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar la tabla de datos
        table = soup.find('table', {'class': 'taula-dades'})
        if not table:
            return None
            
        rows = table.find_all('tr')
        if len(rows) < 2:
            return None
        
        # La segunda fila generalmente contiene los datos más recientes
        data_row = rows[1]
        cells = data_row.find_all('td')
        
        if len(cells) < 9:
            return None
        
        # Extraer datos con manejo seguro de (s/d)
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
        print(f"Error obteniendo datos: {e}")
        return None

def generate_rss():
    data = get_meteo_data()
    
    if not data:
        # Datos de respaldo si no se pueden obtener
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
    
    # Obtener timestamp actual
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    timestamp = int(now.timestamp())
    
    # Formatear datos
    title_ca = f"METEOCAT CET  |  {data['hora']}  |  Temp:{data['temp']}C  |  Max:{data['max_temp']}C  |  Min:{data['min_temp']}C  |  Hum:{data['hum']}%  |  Vent:{data['wind']}km/h  |  Rafega:{data['gust']}km/h  |  Precip:{data['precip']}mm  |  Pres:{data['pressure']}hPa"
    title_en = f" |  Temp:{data['temp']}C  |  Max:{data['max_temp']}C  |  Min:{data['min_temp']}C  |  Hum:{data['hum']}%  |  Wind:{data['wind']}km/h  |  Gust:{data['gust']}km/h  |  Precip:{data['precip']}mm  |  Press:{data['pressure']}hPa"
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat RSS</title>
  <link>https://www.meteo.cat</link>
  <description>Automated meteorological data - Dades meteorològiques automàtiques - Timestamp: {timestamp}</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{title_ca}{title_en}  |  ⌚ {timestamp}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    # Guardar archivo RSS
    with open('meteo.rss', 'w', encoding='utf-8') as f:
        f.write(rss_content)

if __name__ == "__main__":
    generate_rss()
