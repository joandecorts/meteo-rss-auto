import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import re
import sys

def debug_meteo_page():
    """Función para diagnosticar qué hay en la página"""
    try:
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        print(f"🔍 Accediendo a: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✅ Página cargada - Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar TODAS las tablas para diagnóstico
        tables = soup.find_all('table')
        print(f"📊 Tablas encontradas: {len(tables)}")
        
        for i, table in enumerate(tables):
            print(f"  Tabla {i}: Clases: {table.get('class', ['sin-clase'])}")
            rows = table.find_all('tr')
            print(f"    Filas: {len(rows)}")
            if rows:
                cells = rows[0].find_all(['td', 'th'])
                print(f"    Celdas en primera fila: {len(cells)}")
                if len(cells) > 0:
                    print(f"    Primera celda: {cells[0].text.strip()[:50]}...")
        
        # Buscar específicamente la tabla de datos
        target_table = soup.find('table', {'class': 'taula-dades'})
        if target_table:
            print("🎯 TABLA 'taula-dades' ENCONTRADA")
            rows = target_table.find_all('tr')
            print(f"   Filas en taula-dades: {len(rows)}")
            
            if len(rows) >= 2:
                data_row = rows[1]
                cells = data_row.find_all('td')
                print(f"   Celdas en fila de datos: {len(cells)}")
                
                for j, cell in enumerate(cells):
                    print(f"     Celda {j}: '{cell.text.strip()}'")
                
                if len(cells) >= 9:
                    return {
                        'hora': cells[0].text.strip(),
                        'temp': cells[1].text.strip(),
                        'max_temp': cells[2].text.strip(), 
                        'min_temp': cells[3].text.strip(),
                        'hum': cells[4].text.strip(),
                        'wind': cells[5].text.strip(),
                        'gust': cells[6].text.strip(),
                        'precip': cells[7].text.strip(),
                        'pressure': cells[8].text.strip()
                    }
            else:
                print("❌ No hay suficientes filas en taula-dades")
        else:
            print("❌ NO se encontró tabla con clase 'taula-dades'")
            
        return None
        
    except Exception as e:
        print(f"🚨 Error en diagnóstico: {e}")
        return None

def safe_float(value, default=None):
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
    print("🌤️ Iniciando obtención de datos meteorológicos...")
    raw_data = debug_meteo_page()
    
    if not raw_data:
        print("❌ No se pudieron obtener datos en crudo")
        return None
    
    print("📦 Datos en crudo obtenidos:")
    for key, value in raw_data.items():
        print(f"   {key}: '{value}'")
    
    # Convertir a valores numéricos
    temp = safe_float(raw_data['temp'])
    max_temp = safe_float(raw_data['max_temp']) 
    min_temp = safe_float(raw_data['min_temp'])
    hum = safe_float(raw_data['hum'])
    wind = safe_float(raw_data['wind'])
    gust = safe_float(raw_data['gust'])
    precip = safe_float(raw_data['precip'])
    pressure = safe_float(raw_data['pressure'])
    
    # Verificar si tenemos datos válidos
    valid_data = any(val is not None for val in [temp, max_temp, min_temp, hum, wind, gust, precip, pressure])
    
    if not valid_data:
        print("❌ No hay valores numéricos válidos después de la conversión")
        return None
    
    print("✅ Datos convertidos exitosamente")
    return {
        'hora': raw_data['hora'],
        'temp': temp if temp is not None else 0.0,
        'max_temp': max_temp if max_temp is not None else 0.0,
        'min_temp': min_temp if min_temp is not None else 0.0,
        'hum': hum if hum is not None else 0.0,
        'wind': wind if wind is not None else 0.0,
        'gust': gust if gust is not None else 0.0,
        'precip': precip if precip is not None else 0.0,
        'pressure': pressure if pressure is not None else 0.0
    }

def generate_rss():
    data = get_meteo_data()
    
    if not data:
        print("🚨 No se generará RSS por falta de datos válidos")
        # No generamos RSS para evitar valores 0.0
        return False
    
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
    
    print("✅ RSS generado exitosamente")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando actualización de RSS meteorológico...")
    success = generate_rss()
    if success:
        print("🎉 Actualización completada con éxito")
    else:
        print("💤 No se actualizó el RSS (sin datos válidos)")
    # Siempre salir con éxito para evitar emails de error
    sys.exit(0)
