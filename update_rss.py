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
        
        # Buscar TODAS las tablas por si ha cambiado la clase
        tables = soup.find_all('table')
        print(f"📊 Tablas encontradas: {len(tables)}")
        
        target_table = None
        for table in tables:
            if 'tblperiode' in table.get('class', []):
                target_table = table
                break
        
        if not target_table:
            print("❌ No se encontró tabla 'tblperiode', probando con cualquier tabla...")
            target_table = tables[0] if tables else None
            
        if not target_table:
            print("❌ No hay tablas en la página")
            return None
            
        rows = target_table.find_all('tr')
        print(f"📊 Filas en la tabla: {len(rows)}")
        
        # DIAGNÓSTICO: Mostrar las primeras 3 filas para ver la estructura
        print("🔍 Mostrando estructura de las primeras 3 filas:")
        for i in range(min(3, len(rows))):
            cells = rows[i].find_all(['td', 'th'])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            print(f"   Fila {i}: {cell_texts}")
        
        # Buscar desde la ÚLTIMA fila hacia arriba
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all('td')
            
            if len(cells) >= 6:  # Menos columnas requeridas
                periodo_cell = cells[0].get_text(strip=True)
                
                # Verificar si es un período válido
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periodo_cell):
                    print(f"🔍 Analizando fila {i}: {periodo_cell}")
                    
                    # Función simple para extraer números
                    def extract_number(cell_index):
                        try:
                            text = cells[cell_index].get_text(strip=True)
                            if not text or '(s/d)' in text:
                                return None
                            # Buscar el primer número en el texto
                            match = re.search(r'(-?\d+\.?\d*)', text.replace(',', '.'))
                            return float(match.group(1)) if match else None
                        except:
                            return None
                    
                    # Extraer datos básicos
                    temp = extract_number(1)  # Temperatura
                    hum = extract_number(4)   # Humedad
                    
                    print(f"   📊 Datos crudos - Temp: {temp}, Hum: {hum}")
                    
                    # Si tenemos al menos un dato, usar esta fila
                    if temp is not None or hum is not None:
                        print(f"✅ FILA VÁLIDA ENCONTRADA: {periodo_cell}")
                        
                        # Extraer el resto de datos
                        max_temp = extract_number(2) or temp
                        min_temp = extract_number(3) or temp
                        precip = extract_number(5) or 0.0
                        wind = extract_number(6) or 0.0
                        
                        # Para ráfagas y presión, intentar con índices variables
                        gust = extract_number(7) or extract_number(8) or 0.0
                        pressure = extract_number(9) or extract_number(10) or 0.0
                        
                        # Ajustar período a hora local
                        periodo_ajustado = adjust_period_time(periodo_cell)
                        
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
                        print(f"❌ Fila sin datos válidos, continuando...")
        
        print("❌ No se encontró ninguna fila con datos")
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
            print(f"🕒 Período ajustado: {period_str} → {adjusted}")
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
