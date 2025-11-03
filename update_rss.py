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
        
        # DIAGNÓSTICO COMPLETO: Mostrar TODAS las filas con datos
        print("\n🔍 DIAGNÓSTICO COMPLETO DE LA TABLA:")
        print("=" * 80)
        
        valid_periods = []
        
        for i in range(1, min(15, len(rows))):
            data_row = rows[i]
            cells = data_row.find_all('td')
            
            if len(cells) >= 11:
                hora = cells[0].text.strip()
                
                # Verificar si es una fila de datos válida (formato de hora)
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', hora):
                    # Extraer datos para diagnóstico
                    temp_text = cells[1].text.strip()
                    hum_text = cells[4].text.strip()
                    temp = safe_float(temp_text)
                    hum = safe_float(hum_text)
                    
                    # Determinar estado
                    has_s_d = '(s/d)' in temp_text or '(s/d)' in hum_text
                    has_valid_data = temp is not None and hum is not None
                    in_range = has_valid_data and (5 <= temp <= 40 and 10 <= hum <= 100)
                    
                    status = "✅ VÁLIDO" if (has_valid_data and in_range and not has_s_d) else "❌ INVÁLIDO"
                    
                    print(f"Fila {i:2}: {hora} | TM:'{temp_text}'→{temp} | HR:'{hum_text}'→{hum} | {status}")
                    
                    if has_valid_data and in_range and not has_s_d:
                        valid_periods.append({
                            'index': i,
                            'hora': hora,
                            'cells': cells
                        })
        
        print("=" * 80)
        print(f"📋 Períodos válidos encontrados: {len(valid_periods)}")
        
        # ⚡ CORRECCIÓN CRÍTICA: Seleccionar el PRIMER período válido (más reciente)
        if valid_periods:
            selected = valid_periods[0]  # ⚡ SIEMPRE el primero (más reciente)
            i = selected['index']
            cells = selected['cells']
            hora = selected['hora']
            
            print(f"🎯 SELECCIONADO: Fila {i} - Período MÁS RECIENTE: {hora}")
            
            # Extraer todos los datos
            temp = safe_float(cells[1].text)
            max_temp = safe_float(cells[2].text)
            min_temp = safe_float(cells[3].text)
            hum = safe_float(cells[4].text)
            precip = safe_float(cells[5].text)
            wind = safe_float(cells[6].text)
            gust = safe_float(cells[8].text)
            pressure = safe_float(cells[9].text)
            
            print("📊 DATOS DEL PERÍODO MÁS RECIENTE:")
            print(f"   Período oficial: {hora}")
            print(f"   TM (Actual): {temp}°C")
            print(f"   TX (Máxima): {max_temp}°C")
            print(f"   TN (Mínima): {min_temp}°C")
            print(f"   HR (Humedad): {hum}%")
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
        print("❌ No se pudieron obtener datos válidos de ningún período")
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
        # 🎯 FORMATO DEFINITIVO - MANTENIENDO LO QUE ESTÁ BIEN
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
