import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys

def adjust_period_time(period_str):
    """Ajusta el período de UTC a hora local (CET/CEST)"""
    try:
        # Extraer horas del período (formato "HH:MM-HH:MM")
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
            
            # CET = UTC+1, CEST = UTC+2
            is_dst = now_cet.dst() != timedelta(0)
            offset_hours = 2 if is_dst else 1
            
            # Ajustar horas
            start_hour_adj = (start_hour + offset_hours) % 24
            end_hour_adj = (end_hour + offset_hours) % 24
            
            adjusted_period = f"{start_hour_adj:02d}:{start_minute:02d}-{end_hour_adj:02d}:{end_minute:02d}"
            return adjusted_period
        
    except Exception as e:
        print(f"Error ajustando período: {e}")
    
    return period_str

def get_meteo_data():
    try:
        print("🌐 Conectando a Meteo.cat...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            return None
            
        rows = table.find_all('tr')
        print(f"📊 Filas encontradas: {len(rows)}")
        
        # Buscar desde la ÚLTIMA fila hacia arriba
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all('td')
            
            if len(cells) >= 11:
                periodo = cells[0].text.strip()
                
                # Verificar formato de período
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periodo):
                    # Extraer valores numéricos
                    def get_value(cell):
                        text = cell.text.strip()
                        if '(s/d)' in text or not text:
                            return None
                        match = re.search(r'([-]?\d+\.?\d*)', text.replace(',', '.'))
                        return float(match.group(1)) if match else None
                    
                    temp = get_value(cells[1])
                    hum = get_value(cells[4])
                    
                    # Si tenemos al menos temperatura o humedad, es válido
                    if temp is not None or hum is not None:
                        print(f"✅ Período válido encontrado: {periodo}")
                        
                        # Obtener todos los datos
                        max_temp = get_value(cells[2]) or temp
                        min_temp = get_value(cells[3]) or temp
                        precip = get_value(cells[5]) or 0.0
                        wind = get_value(cells[6]) or 0.0
                        gust = get_value(cells[8]) or 0.0
                        pressure = get_value(cells[9]) or 0.0
                        
                        # Ajustar período a hora local
                        periodo_ajustado = adjust_period_time(periodo)
                        
                        return {
                            'periodo': periodo_ajustado,
                            'temp': temp or 0.0,
                            'max_temp': max_temp or 0.0,
                            'min_temp': min_temp or 0.0,
                            'hum': hum or 0.0,
                            'precip': precip,
                            'wind': wind,
                            'gust': gust,
                            'pressure': pressure
                        }
                    else:
                        print(f"❌ Período sin datos: {periodo}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def generate_rss():
    data = get_meteo_data()
    
    # Hora actual
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not data:
        print("❌ No se encontraron datos válidos")
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
    
    print("✅ RSS generado correctamente")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando actualización...")
    success = generate_rss()
    if success:
        print("🎉 Completado")
    else:
        print("💤 No se pudo generar RSS")
    sys.exit(0)
