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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("✅ Conexión exitosa")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            print("❌ No se encontró la tabla")
            return None
            
        rows = table.find_all('tr')
        print(f"📊 Filas encontradas: {len(rows)}")
        
        # Buscar desde la ÚLTIMA fila (la más reciente)
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all('td')
            if len(cells) >= 11:  # Debe tener todas las columnas
                periodo = cells[0].get_text(strip=True)
                
                # Verificar que sea un período válido
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periodo):
                    print(f"🔍 Analizando período: {periodo}")
                    
                    # Extraer los valores directamente
                    temp_text = cells[1].get_text(strip=True)  # TM
                    hum_text = cells[4].get_text(strip=True)   # HRM
                    
                    print(f"   TM: '{temp_text}', HR: '{hum_text}'")
                    
                    # Si hay datos en TM o HRM, usar esta fila
                    if temp_text and temp_text != '(s/d)' and hum_text and hum_text != '(s/d)':
                        print("✅ PERÍODO VÁLIDO CON DATOS")
                        
                        # Convertir a números
                        try:
                            temp = float(temp_text.replace(',', '.'))
                            hum = float(hum_text.replace(',', '.'))
                            max_temp = float(cells[2].get_text(strip=True).replace(',', '.')) if cells[2].get_text(strip=True) not in ['', '(s/d)'] else temp
                            min_temp = float(cells[3].get_text(strip=True).replace(',', '.')) if cells[3].get_text(strip=True) not in ['', '(s/d)'] else temp
                            precip = float(cells[5].get_text(strip=True).replace(',', '.')) if cells[5].get_text(strip=True) not in ['', '(s/d)'] else 0.0
                            wind = float(cells[6].get_text(strip=True).replace(',', '.')) if cells[6].get_text(strip=True) not in ['', '(s/d)'] else 0.0
                            gust = float(cells[8].get_text(strip=True).replace(',', '.')) if cells[8].get_text(strip=True) not in ['', '(s/d)'] else 0.0
                            pressure = float(cells[9].get_text(strip=True).replace(',', '.')) if cells[9].get_text(strip=True) not in ['', '(s/d)'] else 0.0
                            
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
                        print("❌ Período sin datos, buscando anterior...")
                        continue
        
        print("❌ No se encontraron datos válidos")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
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
            
            start_hour_adj = (start_hour + offset_hours) % 24
            end_hour_adj = (end_hour + offset_hours) % 24
            
            adjusted = f"{start_hour_adj:02d}:{start_minute:02d}-{end_hour_adj:02d}:{end_minute:02d}"
            print(f"🕒 Período ajustado: {period_str} UTC → {adjusted} {'CEST' if is_dst else 'CET'}")
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
        print("❌ No se pudieron obtener datos")
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
    
    print("✅ RSS actualizado correctamente")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando actualización RSS...")
    success = generate_rss()
    if success:
        print("🎉 Completado - RSS actualizado")
    else:
        print("💤 No se pudo actualizar el RSS")
    sys.exit(0)
