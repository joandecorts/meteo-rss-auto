import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import re
import sys
import os

print(f"📂 Directorio actual: {os.getcwd()}")
print(f"📄 Archivos en directorio: {os.listdir('.')}")

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
        print("🌐 Conectando a Meteo.cat...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("✅ Conexión exitosa a Meteo.cat")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ⚡ CORRECCIÓN: Buscar la tabla por la clase CORRECTA 'tblperiode'
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            print("❌ No se encontró tabla 'tblperiode'")
            return None
            
        rows = table.find_all('tr')
        if len(rows) < 2:
            print("❌ No hay suficientes filas en la tabla")
            return None
        
        # La segunda fila contiene los datos más recientes (índice 1)
        data_row = rows[1]
        cells = data_row.find_all('td')
        
        if len(cells) < 9:
            print(f"❌ No hay suficientes celdas: {len(cells)}")
            return None
        
        # Extraer datos - ajustar índices según la nueva estructura
        hora = cells[0].text.strip()
        temp = safe_float(cells[1].text)
        max_temp = safe_float(cells[2].text)
        min_temp = safe_float(cells[3].text)
        hum = safe_float(cells[4].text)
        wind = safe_float(cells[5].text)
        gust = safe_float(cells[6].text)
        precip = safe_float(cells[7].text)
        pressure = safe_float(cells[8].text)
        
        print(f"📊 Datos obtenidos - Hora: {hora}, Temp: {temp}°C")
        
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
        print(f"❌ Error obteniendo datos: {e}")
        return None

def generate_rss():
    print("📝 Generando RSS...")
    data = get_meteo_data()
    
    # Obtener timestamp actual
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    timestamp = int(now.timestamp())
    
    # Si no hay datos, usar valores por defecto
    if not data:
        print("⚠️ No se pudieron obtener datos, usando valores por defecto")
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
    
    # Formatear título
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
    try:
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        print("✅ RSS generado exitosamente")
        
        # Verificar que el archivo se creó
        if os.path.exists('meteo.rss'):
            file_size = os.path.getsize('meteo.rss')
            print(f"📁 Archivo meteo.rss creado - Tamaño: {file_size} bytes")
            return True
        else:
            print("❌ ERROR: meteo.rss no se creó")
            return False
            
    except Exception as e:
        print(f"❌ Error guardando RSS: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando actualización de RSS meteorológico...")
    success = generate_rss()
    if success:
        print("🎉 Actualización completada - meteo.rss generado")
        # Listar archivos final para verificación
        print("📋 Archivos finales en directorio:")
        for file in os.listdir('.'):
            print(f"   - {file}")
    else:
        print("❌ Fallo en la actualización")
    sys.exit(0)
