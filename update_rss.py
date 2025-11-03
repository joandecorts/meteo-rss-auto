import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
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

def adjust_period_time(period_str):
    """
    Ajusta el período de UTC a hora local (CET/CEST)
    Ejemplo: "18:00-18:30" (UTC) → "20:00-20:30" (CEST)
    """
    try:
        # Extraer las horas del período
        match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', period_str)
        if match:
            start_hour = int(match.group(1))
            start_minute = int(match.group(2))
            end_hour = int(match.group(3))
            end_minute = int(match.group(4))
            
            # Determinar diferencia horaria (CET = UTC+1, CEST = UTC+2)
            cet = pytz.timezone('CET')
            now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            now_cet = now_utc.astimezone(cet)
            
            # Verificar si es horario de verano (CEST)
            is_dst = now_cet.dst() != timedelta(0)
            offset_hours = 2 if is_dst else 1
            
            print(f"🕒 Diferencia horaria: UTC+{offset_hours} ({'CEST' if is_dst else 'CET'})")
            
            # Ajustar horas
            start_hour_adj = (start_hour + offset_hours) % 24
            end_hour_adj = (end_hour + offset_hours) % 24
            
            adjusted_period = f"{start_hour_adj:02d}:{start_minute:02d}-{end_hour_adj:02d}:{end_minute:02d}"
            print(f"🕒 Período ajustado: {period_str} (UTC) → {adjusted_period} ({'CEST' if is_dst else 'CET'})")
            return adjusted_period
        
    except Exception as e:
        print(f"❌ Error ajustando período: {e}")
    
    return period_str

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
        
        # 🎯 LECTURA ESPECÍFICA DE LAS 5 ÚLTIMAS FILAS
        print("🔍 ANALIZANDO LAS 5 ÚLTIMAS FILAS:")
        last_5_rows = []
        
        # Obtener índices de las últimas 5 filas (excluyendo la cabecera)
        start_index = max(1, len(rows) - 5)
        for i in range(start_index, len(rows)):
            data_row = rows[i]
            cells = data_row.find_all('td')
            
            if len(cells) >= 11:
                hora = cells[0].text.strip()
                
                # Verificar si es una fila de datos válida (formato de hora)
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', hora):
                    # Extraer datos
                    temp = safe_float(cells[1].text, None)
                    max_temp = safe_float(cells[2].text, None)
                    min_temp = safe_float(cells[3].text, None)
                    hum = safe_float(cells[4].text, None)
                    precip = safe_float(cells[5].text, 0.0)
                    wind = safe_float(cells[6].text, 0.0)
                    gust = safe_float(cells[8].text, 0.0)
                    pressure = safe_float(cells[9].text, 0.0)
                    
                    # 🎯 CRITERIOS MÁS FLEXIBLES: Aceptar filas aunque algunos datos sean None
                    # Solo requerimos que al menos temperatura o humedad tengan datos
                    tiene_datos_esenciales = temp is not None or hum is not None
                    
                    # Guardar información de la fila
                    row_data = {
                        'index': i,
                        'hora': hora,
                        'temp': temp,
                        'max_temp': max_temp,
                        'min_temp': min_temp,
                        'hum': hum,
                        'precip': precip,
                        'wind': wind,
                        'gust': gust,
                        'pressure': pressure,
                        'es_valida': tiene_datos_esenciales
                    }
                    
                    last_5_rows.append(row_data)
                    
                    estado = "✅ VÁLIDA" if row_data['es_valida'] else "❌ INVÁLIDA"
                    print(f"📝 Fila {i}: {hora} | TM:{temp}°C | HR:{hum}% | {estado}")
        
        # 🎯 SELECCIONAR LA ÚLTIMA FILA VÁLIDA
        valid_data = None
        for row_data in reversed(last_5_rows):  # Recorrer de más reciente a más antigua
            if row_data['es_valida']:
                valid_data = row_data
                print(f"🎯 SELECCIONADA: Fila {row_data['index']} - Período: {row_data['hora']}")
                break
        
        if valid_data:
            # 🎯 AJUSTAR EL PERÍODO A HORA LOCAL
            adjusted_hora = adjust_period_time(valid_data['hora'])
            
            print("🎯 VALORES EXTRAÍDOS DE LA FILA SELECCIONADA:")
            print(f"   Hora (original): {valid_data['hora']}")
            print(f"   Hora (ajustada): {adjusted_hora}")
            print(f"   TM: {valid_data['temp']}")
            print(f"   TX: {valid_data['max_temp']}")
            print(f"   TN: {valid_data['min_temp']}")
            print(f"   HR: {valid_data['hum']}")
            print(f"   PPT: {valid_data['precip']}")
            print(f"   VVM: {valid_data['wind']}")
            print(f"   VVX: {valid_data['gust']}")
            print(f"   PM: {valid_data['pressure']}")

            # 🎯 VALORES POR DEFECTO MÁS INTELIGENTES
            temp_final = valid_data['temp'] if valid_data['temp'] is not None else 0.0
            max_temp_final = valid_data['max_temp'] if valid_data['max_temp'] is not None else temp_final
            min_temp_final = valid_data['min_temp'] if valid_data['min_temp'] is not None else temp_final
            hum_final = valid_data['hum'] if valid_data['hum'] is not None else 0.0

            # Devolver solo los datos necesarios
            return {
                'hora': adjusted_hora,
                'temp': temp_final,
                'max_temp': max_temp_final,
                'min_temp': min_temp_final,
                'hum': hum_final,
                'precip': valid_data['precip'],
                'wind': valid_data['wind'],
                'gust': valid_data['gust'],
                'pressure': valid_data['pressure']
            }
        else:
            print("❌ No se encontró ninguna fila con datos válidos en las últimas 5 filas")
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
        # 🎯 MEJOR: No usar datos de respaldo fijos, sino intentar calcular el período actual
        # y mostrar que no hay datos disponibles
        current_hour = now.hour
        current_minute = now.minute
        
        # Calcular período actual aproximado
        if current_minute >= 30:
            period_start = f"{current_hour:02d}:30"
            period_end = f"{(current_hour + 1) % 24:02d}:00"
        else:
            period_start = f"{current_hour:02d}:00"
            period_end = f"{current_hour:02d}:30"
        
        base_period = f"{period_start}-{period_end}"
        adjusted_period = adjust_period_time(base_period)
        
        data = {
            'hora': adjusted_period,
            'temp': "N/A",
            'max_temp': "N/A",
            'min_temp': "N/A",
            'hum': "N/A",
            'precip': "N/A",
            'wind': "N/A",
            'gust': "N/A",
            'pressure': "N/A"
        }
        print(f"📊 No hay datos disponibles para el período {adjusted_period}")
    
    # 🎯 FORMATO DEFINITIVO - ESTRUCTURA FINAL
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
