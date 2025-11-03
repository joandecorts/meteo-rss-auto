import requests
import csv
import os
from datetime import datetime
from io import StringIO

def update_rss():
    # Configuración
    csv_url = "https://www.meteo.cat/observacions/xarxa/dades/mesures.csv"
    rss_file = "rss.xml"
    
    try:
        # Descargar CSV
        response = requests.get(csv_url)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        # Leer todas las líneas
        lines = response.text.strip().split('\n')
        
        if len(lines) < 2:
            raise ValueError("CSV vacío o con formato incorrecto")
        
        # Tomar la última línea (datos más recientes)
        last_line = lines[-1]
        
        # Parsear CSV
        reader = csv.reader(StringIO(last_line))
        row = next(reader)
        
        if len(row) < 10:
            raise ValueError(f"Fila con menos columnas de las esperadas: {len(row)}")
        
        # Extraer datos con índices corregidos
        periodo = row[0] if row[0] else "Dades no disponibles"
        tm = row[1] if row[1] else "N/A"
        tx = row[2] if row[2] else "N/A" 
        tn = row[3] if row[3] else "N/A"
        hrm = row[4] if row[4] else "N/A"
        ppt = row[6] if row[6] else "0.0"  # Columna 7
        vvm = row[5] if row[5] else "0.0"  # Columna 6 - Viento
        vvx = row[7] if row[7] else "0.0"  # Columna 8 - Ráfagas  
        pm = row[8] if row[8] else "0.0"   # Columna 9 - Presión
        
        # Hora actual para el título
        current_time = datetime.now().strftime("%H:%M")
        
        # Crear título bilingüe
        title_cat = f"[CAT] Actualitzat {current_time} | {periodo} | Actual:{tm}°C | Màx:{tx}°C | Mín:{tn}°C | Hum:{hrm}% | Precip:{ppt}mm | Vent:{vvm}km/h | Ràfegues:{vvx}km/h | Pressió:{pm}hPa"
        title_gb = f"[GB] Updated {current_time} | {periodo} | Current:{tm}°C | Max:{tx}°C | Min:{tn}°C | Hum:{hrm}% | Precip:{ppt}mm | Wind:{vvm}km/h | Gusts:{vvx}km/h | Pressure:{pm}hPa"
        
        full_title = f"{title_cat} | {title_gb}"
        
    except Exception as e:
        # En caso de error, mostrar mensaje de datos no disponibles
        current_time = datetime.now().strftime("%H:%M")
        title_cat = f"[CAT] Actualitzat {current_time} | Dades no disponibles"
        title_gb = f"[GB] Updated {current_time} | Data not available"
        full_title = f"{title_cat} | {title_gb}"
    
    # Generar RSS
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat RSS</title>
  <link>https://www.meteo.cat</link>
  <description>Automated meteorological data - Dades meteorològiques automàtiques</description>
  <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{full_title}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    # Guardar archivo
    with open(rss_file, 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    return full_title

if __name__ == "__main__":
    result = update_rss()
    print("RSS actualizado:", result)
