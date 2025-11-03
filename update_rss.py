import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import re
import sys
import os

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
        
        # Buscar el PRIMER período con datos válidos (más reciente)
        for i in range(1, min(10, len(rows))):
            data_row = rows[i]
            cells = data_row.find_all('td')
            
            if len(cells) >= 11:
                hora = cells[0].text.strip()
                
                # Verificar si es una fila de datos válida (formato de hora)
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', hora):
                    print(f"🔍 Revisando fila {i} - Período: {hora}")
                    
                    # ⚡ ESTRUCTURA CORREGIDA SEGÚN TU ESPECIFICACIÓN
                    # 0: Período, 1:TM, 2:TX, 3:TN, 4:HRM, 5:PPT, 6:VVM, 7:DVM(no), 8:VVX, 9:PM, 10:RS(no)
                    temp = safe_float(cells[1].text, None)      # TM - Temperatura media
                    max_temp = safe_float(cells[2].text, None)  # TX - Temperatura máxima
                    min_temp = safe_float(cells[3].text, None)  # TN - Temperatura mínima
                    hum = safe_float(cells[4].text, None)       # HRM - Humedad
                    precip = safe_float(cells[5].text, None)    # PPT - Precipitación
                    wind = safe_float(cells[6].text, None)      # VVM - Viento medio
                    gust = safe_float(cells[8].text, None)      # VVX - Ráfagas máximas
                    pressure = safe_float(cells[9].text, None)  # PM - Presión
                    
                    # Verificar si esta fila tiene datos válidos
                    if temp is not None and hum is not None:
                        if 5 <= temp <= 40 and 0 <= hum <= 100:
                            print(f"✅ Fila {i} tiene datos VÁLIDOS")
                            
                            print("📊 DATOS EXTRAÍDOS (estructura corregida):")
                            print(f"   Período oficial: {hora}")
                            print(f"   TM (Actual): {temp}°C")
                            print(f"   TX (Máxima): {max_temp}°C")
                            print(f"   TN (Mínima): {min_temp}°C")
                            print(f"   HRM (Humedad): {hum}%")
                            print(f"   PPT (Precipitación): {precip}mm")
                            print(f"   VVM (Viento): {wind}km/h")
                            print(f"   VVX (Ráfagas): {gust}km/h")
                            print(f"   PM (Presión): {pressure}hPa")
                            
                            return {
                                'hora': hora,
                                'temp': temp,
                                'max_temp': max_temp,
                                'min_temp': min_temp,
                                'hum': hum,
                                'precip': precip,
                                'wind': wind,
                                'gust': gust,
                                'pressure': pressure
                            }
                        else:
                            print(f"⚠️ Fila {i} tiene datos fuera de rango: temp={temp}, hum={hum}")
                    else:
                        print(f"❌ Fila {i} tiene datos INCOMPLETOS (s/d), buscando siguiente período...")
        
        print("❌ No se encontró ningún período con datos válidos")
        return None
        
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return None

def generate_rss():
    data = get_meteo_data()
    
    # Obtener hora actual para ACTUALITZAT/UPDATED
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not data:
        print("❌ No se pudieron obtener datos válidos")
        # Generar mensaje de error
        title = f"[CAT] Actualitzat {current_time} | Dades no disponibles | [GB] Updated {current_time} | Data not available"
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
        # 🎯 FORMATO DEFINITIVO - ESTRUCTURA CORREGIDA
        title = (
            f"[CAT] Actualitzat {current_time} | {data['hora']} | "
            f"Actual:{data['temp']}°C | "
            f"Màx:{data['max_temp']}°C | "
            f"Mín:{data['min_temp']}°C | "
            f"Hum:{data['hum']}% | "
            f"Precip:{data['precip']}mm | "
            f"Vent:{data['wind']}km/h | "
            f"Ràfegues:{data['gust']}km/h | "
            f"Pressió:{data['pressure']}hPa | "
            f"[GB] Updated {current_time} | {data['hora']} | "
            f"Current:{data['temp']}°C | "
            f"Max:{data['max_temp']}°C | "
            f"Min:{data['min_temp']}°C | "
            f"Hum:{data['hum']}% | "
            f"Precip:{data['precip']}mm | "
            f"Wind:{data['wind']}km/h | "
            f"Gusts:{data['gust']}km/h | "
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
        print("🎉 Proceso completado")
    sys.exit(0)
