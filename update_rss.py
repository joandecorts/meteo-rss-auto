import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys

def get_meteo_data():
    try:
        print("🌐 Conectando a Meteo.cat...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("✅ Conexión exitosa")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            print("❌ No se encontró la tabla")
            return None
            
        rows = table.find_all('tr')
        print(f"📊 Total filas: {len(rows)}")
        
        # Recorrer desde la ÚLTIMA fila hasta la PRIMERA
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all('td')
            if len(cells) >= 11:
                periodo = cells[0].get_text(strip=True)
                
                # Verificar si es un período válido
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periodo):
                    print(f"\n🔍 Analizando período: {periodo}")
                    
                    # Leer TODOS los valores en bruto
                    temp_text = cells[1].get_text(strip=True)
                    max_temp_text = cells[2].get_text(strip=True)
                    min_temp_text = cells[3].get_text(strip=True)
                    hum_text = cells[4].get_text(strip=True)
                    precip_text = cells[5].get_text(strip=True)
                    wind_text = cells[6].get_text(strip=True)
                    gust_text = cells[8].get_text(strip=True)
                    
                    print(f"   📊 VALORES CRUDOS:")
                    print(f"   TM: '{temp_text}' | TX: '{max_temp_text}' | TN: '{min_temp_text}'")
                    print(f"   HR: '{hum_text}' | PPT: '{precip_text}'")
                    print(f"   VVM: '{wind_text}' | VVX: '{gust_text}'")
                    
                    # Verificar si hay datos válidos (no vacíos y no s/d)
                    tiene_datos = (temp_text and temp_text != '(s/d)') or (hum_text and hum_text != '(s/d)')
                    
                    if tiene_datos:
                        print("✅ PERÍODO CON DATOS VÁLIDOS")
                        
                        # Convertir a números, usando 0.0 si hay s/d
                        try:
                            temp = float(temp_text.replace(',', '.')) if temp_text and temp_text != '(s/d)' else 0.0
                            max_temp = float(max_temp_text.replace(',', '.')) if max_temp_text and max_temp_text != '(s/d)' else temp
                            min_temp = float(min_temp_text.replace(',', '.')) if min_temp_text and min_temp_text != '(s/d)' else temp
                            hum = float(hum_text.replace(',', '.')) if hum_text and hum_text != '(s/d)' else 0.0
                            precip = float(precip_text.replace(',', '.')) if precip_text and precip_text != '(s/d)' else 0.0
                            wind = float(wind_text.replace(',', '.')) if wind_text and wind_text != '(s/d)' else 0.0
                            gust = float(gust_text.replace(',', '.')) if gust_text and gust_text != '(s/d)' else 0.0
                            pressure = 0.0  # No disponible en esta tabla
                            
                            # Ajustar período a hora local
                            periodo_ajustado = adjust_period_time(periodo)
                            
                            return {
                                'periodo': periodo_ajustado,
                                'temp': temp,
                                'max_temp': max_temp,
                                'min_temp': min_temp,
                                'hum': hum,
                                'precip': precip,
                                'wind': wind,
                                'gust': gust,
                                'pressure': pressure
                            }
                            
                        except ValueError as e:
                            print(f"❌ Error convirtiendo números: {e}")
                            continue
                    else:
                        print("❌ PERÍODO SIN DATOS - Buscando anterior...")
                        continue
        
        print("❌ No se encontró ningún período con datos")
        return None
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return None

def adjust_period_time(period_str):
    """Ajusta período UTC a hora local"""
    try:
        match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', period_str)
        if match:
            start_hour = int(match.group(1))
            start_minute = int(match.group(2))
            end_hour = int(match.group(3))
            end_minute = int(match.group(4))
            
            # Determinar diferencia horaria
            cet = pytz.timezone('CET')
            now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            now_cet = now_utc.astimezone(cet)
            
            is_dst = now_cet.dst() != timedelta(0)
            offset_hours = 2 if is_dst else 1
            
            start_adj = (start_hour + offset_hours) % 24
            end_adj = (end_hour + offset_hours) % 24
            
            adjusted = f"{start_adj:02d}:{start_minute:02d}-{end_adj:02d}:{end_minute:02d}"
            print(f"🕒 AJUSTE: {period_str} UTC → {adjusted} {'CEST' if is_dst else 'CET'}")
            return adjusted
            
    except Exception as e:
        print(f"❌ Error ajustando período: {e}")
    
    return period_str

def generate_rss():
    data = get_meteo_data()
    
    # Hora actual
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not data:
        print("❌ No se pudieron obtener datos - NO se actualiza RSS")
        return False
    
    # Crear título
    title = (
        f"[CAT] Actualitzat {current_time} | {data['periodo']} | "
        f"Actual:{data['temp']}°C | Màx:{data['max_temp']}°C | Mín:{data['min_temp']}°C | "
        f"Hum:{data['hum']}% | Precip:{data['precip']}mm | Vent:{data['wind']}km/h | "
        f"Ràfegues:{data['gust']}km/h | Pressió:{data['pressure']}hPa | "
        f"[GB] Updated {current_time} | {data['periodo']} | "
        f"Current:{data['temp']}°C | Max:{data['max_temp']}°C | Min:{data['min_temp']}°C | "
        f"Hum:{data['hum']}% | Precip:{data['precip']}mm | Wind:{data['wind']}km/h | "
        f"Gusts:{data['gust']}km/h | Pressure:{data['pressure']}hPa"
    )
    
    # Generar RSS
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
    
    # Guardar archivo
    with open('meteo.rss', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    print("✅ RSS ACTUALIZADO CORRECTAMENTE")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando actualización RSS...")
    success = generate_rss()
    if success:
        print("🎉 COMPLETADO - RSS ACTUALIZADO")
    else:
        print("💤 NO SE ACTUALIZÓ - Sin datos válidos")
    sys.exit(0)
