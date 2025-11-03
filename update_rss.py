import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import os

try:
    import pytz
    PYTZ_DISPONIBLE = True
except ImportError:
    PYTZ_DISPONIBLE = False
    print("⚠️  pytz no disponible - utilitzant conversió manual d'hora")

class MeteoCatRSS:
    def __init__(self, codi_estacio="XJ"):
        self.codi_estacio = codi_estacio
        self.base_url = "https://www.meteo.cat/observacions/xema/dades"
    
    def obtenir_hora_oficial_espanya(self):
        """Retorna la hora oficial espanyola (CET/CEST)"""
        if PYTZ_DISPONIBLE:
            # Versió amb pytz (més precisa)
            utc_ara = datetime.utcnow().replace(tzinfo=pytz.utc)
            zona_espanya = pytz.timezone('Europe/Madrid')
            hora_espanya = utc_ara.astimezone(zona_espanya)
            es_horari_estiu = hora_espanya.dst() != timedelta(0)
            zona_horaria = "CEST" if es_horari_estiu else "CET"
            return hora_espanya, zona_horaria
        else:
            # Versió manual (sense pytz)
            utc_ara = datetime.utcnow()
            # Càlcul aproximat horari d'estiu (últim diumenge març a octubre)
            any_actual = utc_ara.year
            inici_estiu = datetime(any_actual, 3, 31) - timedelta(days=(datetime(any_actual, 3, 31).weekday() + 1) % 7)
            fi_estiu = datetime(any_actual, 10, 31) - timedelta(days=(datetime(any_actual, 10, 31).weekday() + 1) % 7)
            
            es_horari_estiu = inici_estiu <= utc_ara.replace(tzinfo=None) < fi_estiu
            zona_horaria = "CEST" if es_horari_estiu else "CET"
            diferencia = timedelta(hours=2) if es_horari_estiu else timedelta(hours=1)
            
            hora_espanya = utc_ara + diferencia
            return hora_espanya, zona_horaria
    
    def obtenir_dades_meteo(self):
        try:
            data_avui = datetime.now().strftime("%Y-%m-%d")
            params = {'codi': self.codi_estacio, 'dia': f"{data_avui}T09:30Z"}
            
            print(f"🔗 Consultant Meteo.cat...")
            response = requests.get(self.base_url, params=params, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            taules = soup.find_all('table')
            
            if len(taules) < 3:
                return None
                
            taula_dades = taules[2]
            dades = []
            files = taula_dades.find_all('tr')[1:]
            
            for fila in files:
                elements = fila.find_all(['td', 'th'])
                if len(elements) >= 11:
                    periode = elements[0].get_text(strip=True)
                    tm = elements[1].get_text(strip=True)
                    
                    if not periode or ':' not in periode or '(s/d)' in tm or 's/d' in tm.lower():
                        continue
                    
                    dades.append({
                        'periode': periode, 'tm': tm,
                        'tx': elements[2].get_text(strip=True),
                        'tn': elements[3].get_text(strip=True),
                        'hrm': elements[4].get_text(strip=True),
                        'ppt': elements[5].get_text(strip=True),
                        'vvm': elements[6].get_text(strip=True),
                        'vvx': elements[8].get_text(strip=True),
                        'pm': elements[9].get_text(strip=True).replace('.0', '')
                    })
            
            if dades:
                print(f"📊 {len(dades)} períodes vàlids")
                return dades[-1]  # Últim període
            
            print("ℹ️  No s'han trobat dades vàlides")
            return None
            
        except Exception as e:
            print(f"❌ Error obtenint dades: {e}")
            return None
    
    def generar_rss_complet(self):
        dades = self.obtenir_dades_meteo()
        hora_espanya, zona_horaria = self.obtenir_hora_oficial_espanya()
        data_rss = hora_espanya.strftime('%a, %d %b %Y %H:%M:%S') + ' ' + zona_horaria
        
        # Timestamp per evitar cache (millora velocitat)
        timestamp = int(time.time())
        
        if not dades:
            title_ca = f"METEOCAT {zona_horaria}  |  Esperant dades actuals..."
            title_en = f"METEOCAT {zona_horaria}  |  Waiting for current data..."
        else:
            periode = dades['periode']
            
            # FORMAT MILLORAT - MÉS ESPAIS
            title_ca = f"METEOCAT {zona_horaria}  |  {periode}  |  Temp:{dades['tm']}C  |  Max:{dades['tx']}C  |  Min:{dades['tn']}C  |  Hum:{dades['hrm']}%  |  Vent:{dades['vvm']}km/h  |  Rafega:{dades['vvx']}km/h  |  Precip:{dades['ppt']}mm  |  Pres:{dades['pm']}hPa"
            title_en = f"METEOCAT {zona_horaria}  |  {periode}  |  Temp:{dades['tm']}C  |  Max:{dades['tx']}C  |  Min:{dades['tn']}C  |  Hum:{dades['hrm']}%  |  Wind:{dades['vvm']}km/h  |  Gust:{dades['vvx']}km/h  |  Precip:{dades['ppt']}mm  |  Press:{dades['pm']}hPa"
        
        rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat RSS</title>
  <link>https://www.meteo.cat</link>
  <description>Automated meteorological data - Dades meteorològiques automàtiques</description>
  <lastBuildDate>{data_rss}</lastBuildDate>
  
  <!-- Versió catalana -->
  <item>
    <title>{title_ca}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{data_rss}</pubDate>
  </item>
  
  <!-- English version -->
  <item>
    <title>{title_en}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{data_rss}</pubDate>
  </item>
</channel>
</rss>'''
        
        # Guardar arxiu
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        print(f"✅ RSS actualitzat: {title_ca}")
        print(f"🕒 Timestamp: {timestamp}")
        return True

# Executar
if __name__ == "__main__":
    meteo = MeteoCatRSS()
    meteo.generar_rss_complet()