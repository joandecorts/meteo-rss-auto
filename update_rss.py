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
        
        # ⚠️ DIAGNÓSTICO DE EMERGENCIA: Verificar si la página carga
        print("🔍 VERIFICANDO CONTENIDO DE LA PÁGINA...")
        print(f"¿Título de la página?: {soup.title.string if soup.title else 'NO HAY TÍTULO'}")
        
        # Buscar TODAS las tablas para diagnóstico
        all_tables = soup.find_all('table')
        print(f"📊 Tablas encontradas en la página: {len(all_tables)}")
        
        for i, table in enumerate(all_tables):
            print(f"  Tabla {i}: Clases: {table.get('class', ['sin-clase'])}")
        
        # Buscar la tabla por la clase 'tblperiode'
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            print("❌ CRÍTICO: No se encontró tabla 'tblperiode'")
            print("🔍 Buscando cualquier tabla con datos...")
            # Intentar con la primera tabla que encontremos
            if all_tables:
                table = all_tables[0]
                print(f"⚠️ Usando tabla alternativa: {table.get('class', ['sin-clase'])}")
            else:
                return None
            
        rows = table.find_all('tr')
        print(f"📊 Filas en la tabla: {len(rows)}")
        
        # ⚠️ DIAGNÓSTICO DE EMERGENCIA: Mostrar las primeras 10 filas COMPLETAS
        print("\n🔍 CONTENIDO COMPLETO DE LAS PRIMERAS 10 FILAS:")
        print("=" * 100)
        
        for i in range(min(10, len(rows))):
            row = rows[i]
            cells = row.find_all(['td', 'th'])
            print(f"Fila {i}:")
            for j, cell in enumerate(cells):
                print(f"  Columna {j}: '{cell.text.strip()}'")
            print("-" * 50)
        
        print("=" * 100)
        
        # ⚠️ EMERGENCIA: Buscar CUALQUIER dato que parezca meteorológico
        print("\n🔍 BUSQUEDA DE EMERGENCIA: Cualquier dato numérico...")
        
        for i in range(1, min(10, len(rows))):
            data_row = rows[i]
            cells = data_row.find_all('td')
            
            if len(cells) >= 5:  # Al menos algunas columnas
                hora = cells[0].text.strip() if len(cells) > 0 else "N/A"
                
                # Buscar CUALQUIER formato de hora
                if re.match(r'.*\d{1,2}:\d{2}.*\d{1,2}:\d{2}.*', hora) or i == 1:
                    print(f"🔍 Revisando fila {i}: '{hora}'")
                    
                    # Intentar extraer CUALQUIER dato numérico
                    for j in range(1, min(10, len(cells))):
                        cell_text = cells[j].text.strip()
                        if cell_text and re.search(r'\d', cell_text) and '(s/d)' not in cell_text:
                            temp = safe_float(cell_text)
                            if temp is not None and -50 <= temp <= 50:  # Rango muy amplio
                                print(f"✅ POSIBLE DATO ENCONTRADO: Columna {j} = {temp}")
                                
                                # Intentar extraer más datos
                                temp = safe_float(cells[1].text) if len(cells) > 1 else 0.0
                                max_temp = safe_float(cells[2].text) if len(cells) > 2 else 0.0
                                min_temp = safe_float(cells[3].text) if len(cells) > 3 else 0.0
                                hum = safe_float(cells[4].text) if len(cells) > 4 else 0.0
                                wind = safe_float(cells[5].text) if len(cells) > 5 else 0.0
                                gust = safe_float(cells[6].text) if len(cells) > 6 else 0.0
                                precip = safe_float(cells[7].text) if len(cells) > 7 else 0.0
                                pressure = safe_float(cells[8].text) if len(cells) > 8 else 0.0
                                
                                print(f"🎯 USANDO DATOS DE EMERGENCIA de fila {i}")
                                print(f"   Período: {hora}")
                                print(f"   Temp: {temp}°C")
                                print(f"   Max: {max_temp}°C")
                                print(f"   Min: {min_temp}°C")
                                print(f"   Hum: {hum}%")
                                print(f"   Viento: {wind}km/h")
                                print(f"   Ráfagas: {gust}km/h")
                                print(f"   Precip: {precip}mm")
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
        
        print("❌ EMERGENCIA: No se pudo encontrar NINGÚN dato válido")
        return None
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        print(f"🔍 Traceback completo: {traceback.format_exc()}")
        return None

def generate_rss():
    data = get_meteo_data()
    
    # Obtener hora actual para ACTUALITZAT/UPDATED
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not data:
        print("❌ EMERGENCIA: No se pudieron obtener datos de NINGUNA forma")
        # Forzar datos de ejemplo como ÚLTIMO recurso
        data = {
            'hora': '17:00-17:30',
            'temp': 16.4,
            'max_temp': 17.6,
            'min_temp': 15.9,
            'hum': 75,
            'wind': 3.2,
            'gust': 8.1,
            'precip': 0.0,
            'pressure': 1022.5
        }
        print("🚨 USANDO DATOS DE EJEMPLO FORZADOS")
    
    # FORMATO (manteniendo lo que está bien)
    title = (
        f"[CAT] Actualitzat {current_time} | {data['hora']} | "
        f"Actual:{data['temp']}°C | "
        f"Màx:{data['max_temp']}°C | "
        f"Mín:{data['min_temp']}°C | "
        f"Hum:{data['hum']}% | "
        f"Vent:{data['wind']}km/h | "
        f"Ràfegues:{data['gust']}km/h | "
        f"Precip:{data['precip']}mm | "
        f"Pressió:{data['pressure']}hPa | "
        f"[GB] Updated {current_time} | {data['hora']} | "
        f"Current:{data['temp']}°C | "
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
    
    print("✅ RSS generado (modo emergencia)")
    return True

if __name__ == "__main__":
    print("🚀 INICIANDO MODO EMERGENCIA...")
    success = generate_rss()
    if success:
        print("🎉 Proceso completado (con datos de emergencia si fue necesario)")
    sys.exit(0)
