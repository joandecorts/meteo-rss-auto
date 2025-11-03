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

def debug_table_structure():
    """Función para diagnosticar la estructura real de la tabla"""
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
            print("❌ No se encontró tabla 'tblperiode'")
            return None
            
        rows = table.find_all('tr')
        print(f"📊 Filas encontradas en la tabla: {len(rows)}")
        
        # Analizar la estructura de las primeras filas
        for i, row in enumerate(rows[:3]):  # Solo las primeras 3 filas
            cells = row.find_all(['td', 'th'])
            print(f"🔍 Fila {i}: {len(cells)} celdas")
            for j, cell in enumerate(cells):
                print(f"   Celda {j}: '{cell.text.strip()}'")
            print("---")
        
        return rows
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        return None

def get_meteo_data():
    try:
        print("🔍 Iniciando diagnóstico de tabla...")
        rows = debug_table_structure()
        
        if not rows or len(rows) < 2:
            print("❌ No hay suficientes filas para extraer datos")
            return None
        
        # La PRIMERA fila de datos (después de los headers) suele ser la más reciente
        # Probemos con diferentes índices hasta encontrar los datos correctos
        data_row = None
        data_cells = None
        
        # Intentar con la fila 1 (índice 1)
        if len(rows) > 1:
            data_row = rows[1]
            data_cells = data_row.find_all('td')
            print(f"📝 Probando fila 1: {len(data_cells)} celdas")
            if len(data_cells) >= 9:
                for j, cell in enumerate(data_cells[:10]):  # Primeras 10 celdas
                    print(f"   Celda {j}: '{cell.text.strip()}'")
        
        # Si la fila 1 no tiene datos válidos, probar con la fila 2
        if not data_cells or len(data_cells) < 9:
            if len(rows) > 2:
                data_row = rows[2]
                data_cells = data_row.find_all('td')
                print(f"📝 Probando fila 2: {len(data_cells)} celdas")
                if len(data_cells) >= 9:
                    for j, cell in enumerate(data_cells[:10]):
                        print(f"   Celda {j}: '{cell.text.strip()}'")
        
        if not data_cells or len(data_cells) < 9:
            print("❌ No se encontraron suficientes celdas de datos")
            return None
        
        # Extraer datos - AJUSTAR ESTOS ÍNDICES SEGÚN EL DIAGNÓSTICO
        hora = data_cells[0].text.strip() if len(data_cells) > 0 else "Última hora"
        temp = safe_float(data_cells[1].text) if len(data_cells) > 1 else 0.0
        max_temp = safe_float(data_cells[2].text) if len(data_cells) > 2 else 0.0
        min_temp = safe_float(data_cells[3].text) if len(data_cells) > 3 else 0.0
        hum = safe_float(data_cells[4].text) if len(data_cells) > 4 else 0.0
        wind = safe_float(data_cells[5].text) if len(data_cells) > 5 else 0.0
        gust = safe_float(data_cells[6].text) if len(data_cells) > 6 else 0.0
        precip = safe_float(data_cells[7].text) if len(data_cells) > 7 else 0.0
        pressure = safe_float(data_cells[8].text) if len(data_cells) > 8 else 0.0
        
        print("📊 Datos extraídos:")
        print(f"   Hora: {hora}")
        print(f"   Temp: {temp}°C")
        print(f"   Max: {max_temp}°C")
        print(f"   Min: {min_temp}°C")
        print(f"   Hum: {hum}%")
        print(f"   Viento: {wind}km/h")
        print(f"   Ráfagas: {gust}km/h")
        print(f"   Precipitación: {precip}mm")
        print(f"   Presión: {pressure}hPa")
        
        # Validar que los datos sean razonables
        if temp < -50 or temp > 50 or hum < 0 or hum > 100:
            print("⚠️ Datos fuera de rango, posible error en los índices")
            return None
        
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
    timestamp = int(now.timestamp())
    
    # Si no hay datos válidos, usar valores por defecto con nota
    if not data:
        print("⚠️ Usando datos por defecto por error en extracción")
        data = {
            'hora': 'Última hora',
            'temp': 0.0,
            'max_temp': 0.0,
            'min_temp': 0.0,
            'hum': 0.0,
            'wind': 0.0,
            'gust': 0.0,
            'precip': 0.0,
            'pressure': 0.0,
            'note': '⚠️ DADES TEMPORALMENT NO DISPONIBLES'
        }
    
    # FORMATO CORREGIDO CON [CAT] y [GB]
    if data.get('note'):
        title = f"[CAT] {data['hora']} | {data['note']} | [GB] {data['hora']} | {data['note']}"
    else:
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
    
    print("✅ RSS generado exitosamente")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando actualización de RSS meteorológico...")
    success = generate_rss()
    if success:
        print("🎉 Actualización completada")
    else:
        print("❌ Fallo en la actualización")
    sys.exit(0)
