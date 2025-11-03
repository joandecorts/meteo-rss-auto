import requests
import csv
from datetime import datetime
from io import StringIO

def update_rss():
    # URL que funcionava abans
    csv_url = "https://www.meteo.cat/observacions/xarxa/dades/mesures.csv"
    rss_file = "meteo.rss"
    
    try:
        # Descarregar CSV
        response = requests.get(csv_url)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        # Llegir dades - AQUESTA PART FUNCIONAVA
        lines = response.text.strip().split('\n')
        last_line = lines[-1]  # Última línia
        
        # Parsejar CSV
        reader = csv.reader(StringIO(last_line))
        row = next(reader)
        
        # ÍNDEXS ORIGINALS QUE FUNCIONAVEN:
        # 0=Període, 1=TM, 2=TX, 3=TN, 4=HRM, 5=VVM, 6=PPT, 7=VVX, 8=PM
        periodo = row[0]
        tm = row[1]    # Temperatura actual
        tx = row[2]    # Temperatura màxima  
        tn = row[3]    # Temperatura mínima
        hrm = row[4]   # Humitat
        vvm = row[5]   # Vent mitjà
        ppt = row[6]   # Precipitació
        vvx = row[7]   # Ràfegues
        pm = row[8]    # Pressió
        
        # Hora actual
        current_time = datetime.now().strftime("%H:%M")
        
        # Crear títol bilingüe
        title_cat = f"[CAT] Actualitzat {current_time} | {periodo} | Actual:{tm}°C | Màx:{tx}°C | Mín:{tn}°C | Hum:{hrm}% | Precip:{ppt}mm | Vent:{vvm}km/h | Ràfegues:{vvx}km/h | Pressió:{pm}hPa"
        title_gb = f"[GB] Updated {current_time} | {periodo} | Current:{tm}°C | Max:{tx}°C | Min:{tn}°C | Hum:{hrm}% | Precip:{ppt}mm | Wind:{vvm}km/h | Gusts:{vvx}km/h | Pressure:{pm}hPa"
        
        full_title = f"{title_cat} | {title_gb}"
        
    except Exception as e:
        # En cas d'error
        current_time = datetime.now().strftime("%H:%M")
        title_cat = f"[CAT] Actualitzat {current_time} | Error: {str(e)}"
        title_gb = f"[GB] Updated {current_time} | Error: {str(e)}"
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
    
    # Guardar arxiu
    with open(rss_file, 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    return full_title

if __name__ == "__main__":
    result = update_rss()
    print("RSS actualizado:", result)
