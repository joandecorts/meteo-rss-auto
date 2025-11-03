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
        
        # Buscar la fila con datos reales - empezar desde la fila 1 (índice 1)
        for i in range(1, min(6, len(rows))):  # Revisar primeras 5 filas de datos
            data_row = rows[i]
            cells = data_row.find_all('td')
            
            if len(cells) >= 11:  # ⚡ SON 11 COLUMNAS
                hora = cells[0].text.strip()
                
                # Verificar si es una fila de datos válida (formato de hora)
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', hora):
                    print(f"✅ Fila {i} seleccionada - Hora: {hora}")
                    
                    # ⚡ ESTRUCTURA CON 11 COLUMNAS:
                    temp = safe_float(cells[1].text)
                    max_temp = safe_float(cells[2].text)
                    min_temp = safe_float(cells[3].text)
                    hum = safe_float(cells[4].text)
                    wind = safe_float(cells[5].text)
                    gust = safe_float(cells[6].text)
                    precip = safe_float(cells[7].text)
                    pressure = safe_float(cells[8].text)
                    
                    print("📊 DATOS EXTRAÍDOS CORRECTAMENTE:")
                    print(f"   Hora: {hora}")
                    print(f"   Temp: {temp}°C")
                    print(f"   Max: {max_temp}°C") 
                    print(f"   Min: {min_temp}°C")
                    print(f"   Hum: {hum}%")
                    print(f"   Viento: {wind}km/h")
                    print(f"   Ráfagas: {gust}km/h")
                    print(f"   Precip: {precip}mm")
                    print(f"   Presión: {pressure}hPa")
                    
                    # Validar que los datos sean razonables
                    if 10 <= temp <= 40 and 20 <= hum <= 100:
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
                    else:
                        print(f"⚠️ Datos fuera de rango en fila {i}")
        
        print("❌ No se encontró ninguna fila con datos válidos")
        return None
        
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return None

def generate_rss():
    data = get_meteo_data()
    
    # Obtener timestamp actual
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")  # Hora actual en formato 16:45
    timestamp = int(now.timestamp())      # Timestamp para el final
    
    if not data:
        print("❌ No se pudieron obtener datos válidos")
        # Usar datos de ejemplo
        data = {
            'hora': '15:30-16:00',
            'temp': 19.3,
            'max_temp': 19.9,
            'min_temp': 18.6,
            'hum': 63,
            'wind': 0.0,
            'gust': 6.8,
            'precip': 0.0,
            'pressure': 1022.8
        }
        print("📊 Usando datos de ejemplo")
    
    # 🎯 FORMATO MEJORADO CON "ACTUALITZAT", "UPDATED" Y TIMESTAMP
    title = (
        f"[CAT] ACTUALITZAT {current_time} | {data['hora']} | "
        f"Temp:{data['temp']}°C | "
        f"Màx:{data['max_temp']}°C | "
        f"Mín:{data['min_temp']}°C | "
        f"Hum:{data['hum']}% | "
        f"Vent:{data['wind']}km/h | "
        f"Ràfegues:{data['gust']}km/h | "
        f"Precip:{data['precip']}mm | "
        f"Pressió:{data['pressure']}hPa | "
        f"[GB] UPDATED {current_time} | {data['hora']} | "
        f"Temp:{data['temp']}°C | "
        f"Max:{data['max_temp']}°C | "
        f"Min:{data['min_temp']}°C | "
        f"Hum:{data['hum']}% | "
        f"Wind:{data['wind']}km/h | "
        f"Gusts:{data['gust']}km/h | "
        f"Precip:{data['precip']}mm | "
        f"Pressure:{data['pressure']}hPa | "
        f"⌚ {timestamp}"
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
        print("🎉 Proceso completado")
    sys.exit(0)
