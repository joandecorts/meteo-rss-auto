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

def find_correct_data_row(rows):
    """Encuentra automáticamente la fila con datos meteorológicos reales"""
    for i, row in enumerate(rows):
        cells = row.find_all('td')
        if len(cells) >= 9:
            # Verificar si la primera celda tiene formato de hora (ej: "14:00-14:30")
            hora_cell = cells[0].text.strip()
            if re.match(r'\d{1,2}:\d{2}-\d{1,2}:\d{2}', hora_cell):
                # Verificar que los datos sean razonables
                temp = safe_float(cells[1].text, None)
                hum = safe_float(cells[4].text, None)
                
                if temp is not None and hum is not None:
                    if -20 <= temp <= 50 and 0 <= hum <= 100:
                        print(f"✅ Fila {i} seleccionada - Datos válidos encontrados")
                        return cells
                    else:
                        print(f"⚠️ Fila {i} tiene datos fuera de rango: temp={temp}, hum={hum}")
    
    print("❌ No se encontró ninguna fila con datos válidos")
    return None

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
        
        # Buscar la tabla por la clase 'tblperiode'
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            print("❌ No se encontró tabla 'tblperiode'")
            return None
            
        rows = table.find_all('tr')
        print(f"📊 Total de filas en la tabla: {len(rows)}")
        
        # Encontrar automáticamente la fila correcta
        data_cells = find_correct_data_row(rows)
        
        if not data_cells:
            print("❌ No se pudieron encontrar datos válidos")
            return None
        
        # Extraer datos de las celdas correctas
        hora = data_cells[0].text.strip()
        temp = safe_float(data_cells[1].text)
        max_temp = safe_float(data_cells[2].text)
        min_temp = safe_float(data_cells[3].text)
        hum = safe_float(data_cells[4].text)
        wind = safe_float(data_cells[5].text)
        gust = safe_float(data_cells[6].text)
        precip = safe_float(data_cells[7].text)
        pressure = safe_float(data_cells[8].text)
        
        print("📊 DATOS METEOROLÓGICOS REALES ENCONTRADOS:")
        print(f"   Hora: {hora}")
        print(f"   Temperatura: {temp}°C")
        print(f"   Máxima: {max_temp}°C")
        print(f"   Mínima: {min_temp}°C")
        print(f"   Humedad: {hum}%")
        print(f"   Viento: {wind}km/h")
        print(f"   Ráfagas: {gust}km/h")
        print(f"   Precipitación: {precip}mm")
        print(f"   Presión: {pressure}hPa")
        
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
    data = get_meteo_data()
    
    # Obtener timestamp actual
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    
    # Si no hay datos válidos, mostrar mensaje de error
    if not data:
        print("❌ No se pudieron obtener datos meteorológicos")
        # Generar RSS con mensaje de error
        title = "[CAT] Error temporal | No es poden obtenir dades | [GB] Temporary error | Cannot get data"
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
    else:
        # FORMATO CORREGIDO CON DATOS REALES
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
    
    print("✅ RSS generado")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando actualización de RSS meteorológico...")
    success = generate_rss()
    if success:
        print("🎉 Proceso completado")
    sys.exit(0)
