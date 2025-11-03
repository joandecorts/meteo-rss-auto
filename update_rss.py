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
            utc_ara = datetime.utcnow().replace(tzinfo=pytz.utc)
            zona_espanya = pytz.timezone('Europe/Madrid')
            hora_espanya = utc_ara.astimezone(zona_espanya)
            es_horari_estiu = hora_espanya.dst() != timedelta(0)
            zona_horaria = "CEST" if es_horari_estiu else "CET"
            return hora_espanya, zona_horaria
        else:
            utc_ara = datetime.utcnow()
            any_actual = utc_ara.year
            inici_estiu = datetime(any_actual, 3, 31) - timedelta(days=(datetime(any_actual, 3, 31).weekday() + 1) % 7)
            fi_estiu = datetime(any_actual, 10, 31) - timedelta(days=(datetime(any_actual, 10, 31).weekday() + 1) % 7)
            
            es_horari_estiu = inici_estiu <= utc_ara.replace(tzinfo=None) < fi_estiu
            zona_horaria = "CEST" if es_horari_estiu else "CET"
            diferencia = timedelta(hours=2) if es_horari_estiu else timedelta(hours=1)
            
            hora_espanya = utc_ara + diferencia
            return hora_espanya, zona_horaria

    def convertir_periode_gmt_a_local(self, periode_gmt):
        """Converteix un període GMT a hora local espanyola"""
        try:
            hora_inici_gmt, hora_fi_gmt = periode_gmt.split(' - ')
            
            avui = datetime.utcnow().date()
            dt_inici_gmt = datetime.combine(avui, datetime.strptime(hora_inici_gmt, '%H:%M').time())
            dt_fi_gmt = datetime.combine(avui, datetime.strptime(hora_fi_gmt, '%H:%M').time())
            
            if PYTZ_DISPONIBLE:
                zona_espanya = pytz.timezone('Europe/Madrid')
                dt_inici_local = pytz.utc.localize(dt_inici_gmt).astimezone(zona_espanya)
                dt_fi_local = pytz.utc.localize(dt_fi_gmt).astimezone(zona_espanya)
            else:
                es_horari_estiu = self.obtenir_hora_oficial_espanya()[1] == "CEST"
                diferencia = timedelta(hours=2) if es_horari_estiu else timedelta(hours=1)
                dt_inici_local = dt_inici_gmt + diferencia
                dt_fi_local = dt_fi_gmt + diferencia
            
            periode_local = f"{dt_inici_local.strftime('%H:%M')} - {dt_fi_local.strftime('%H:%M')}"
            return periode_local
            
        except Exception as e:
            print(f"⚠️  Error convertint període: {e}")
            return periode_gmt
    
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
                return dades[-1]
            
            print("ℹ️  No s'han trobat dades vàlides")
            return None
            
        except Exception as e:
            print(f"❌ Error obtenint dades: {e}")
            return None
    
    def generar_rss_alternant(self):
        dades = self.obtenir_dades_meteo()
        hora_espanya, zona_horaria = self.obtenir_hora_oficial_espanya()
        data_rss = hora_espanya.strftime('%a, %d %b %Y %H:%M:%S') + ' ' + zona_horaria
        
        # ALTERNAR ENTRE IDIOMES cada 30 segons (basat en el minut actual)
        minut_actual = hora_espanya.minute
        segon_actual = hora_espanya.second
        alternar_idioma = (minut_actual % 2 == 0) or (segon_actual >= 30)
        
        if not dades:
            if alternar_idioma:
                title = "METEOCAT  |  Esperant dades actuals...  |  Waiting for current data..."
            else:
                title = "METEOCAT  |  Waiting for current data...  |  Esperant dades actuals..."
        else:
            periode = self.convertir_periode_gmt_a_local(dades['periode'])
            
            if alternar_idioma:
                # Primer català, després anglès
                title = f"METEOCAT {zona_horaria}  |  {periode}  |  Temp:{dades['tm']}C  |  Max:{dades['tx']}C  |  Min:{dades['tn']}C  |  Hum:{dades['hrm']}%  |  Vent:{dades['vvm']}km/h  |  Rafega:{dades['vvx']}km/h  |  Precip:{dades['ppt']}mm  |  Pres:{dades['pm']}hPa  |  |  Temp:{dades['tm']}C  |  Max:{dades['tx']}C  |  Min:{dades['tn']}C  |  Hum:{dades['hrm']}%  |  Wind:{dades['vvm']}km/h  |  Gust:{dades['vvx']}km/h  |  Precip:{dades['ppt']}mm  |  Press:{dades['pm']}hPa"
            else:
                # Primer anglès, després català
                title = f"METEOCAT {zona_horaria}  |  {periode}  |  Temp:{dades['tm']}C  |  Max:{dades['tx']}C  |  Min:{dades['tn']}C  |  Hum:{dades['hrm']}%  |  Wind:{dades['vvm']}km/h  |  Gust:{dades['vvx']}km/h  |  Precip:{dades['ppt']}mm  |  Press:{dades['pm']}hPa  |  |  Temp:{dades['tm']}C  |  Max:{dades['tx']}C  |  Min:{dades['tn']}C  |  Hum:{dades['hrm']}%  |  Vent:{dades['vvm']}km/h  |  Rafega:{dades['vvx']}km/h  |  Precip:{dades['ppt']}mm  |  Pres:{dades['pm']}hPa"
        
        rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat RSS</title>
  <link>https://www.meteo.cat</link>
  <description>Automated meteorological data - Dades meteorològiques automàtiques</description>
  <lastBuildDate>{data_rss}</lastBuildDate>
  <item>
    <title>{title}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{data_rss}</pubDate>
  </item>
</channel>
</rss>'''
        
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        print(f"✅ RSS alternant: {title[:80]}...")
        return True

if __name__ == "__main__":
    meteo = MeteoCatRSS()
    meteo.generar_rss_alternant()
