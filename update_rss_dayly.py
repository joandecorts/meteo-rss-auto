import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import json
import os

def write_log(message):
    print(message)
    with open('debug_dayly.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def get_daily_summary_from_meteocat(station_code, station_name):
    """Obté el resum diari REAL de MeteoCat (no acumulació local)"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://www.meteo.cat/observacions/xema/dades?codi={station_code}&dia={today}"
        
        write_log(f"🌐 Consultant resum diari REAL: {station_name} [{station_code}]")
        write_log(f"   URL: {url}")
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar totes les taules
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables):
            # Verificar si aquesta taula conté "Resum diari" o "Temperatura"
            table_text = table.get_text()
            if 'Resum diari' in table_text or 'Temperatura' in table_text:
                write_log(f"📊 Taula {i} sembla contenir dades del dia")
                
                # Buscar totes les files de la taula
                rows = table.find_all('tr')
                
                # Diccionari per emmagatzemar valors trobats
                valors = {}
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        valor = cells[1].get_text(strip=True)
                        
                        # Identificar valors clau
                        if 'Temperatura mitjana' in label or 'Temperatura máxima' in label or 'Temperatura mínima' in label or 'Precipitació acumulada' in label:
                            # Extreure número del valor
                            import re
                            num_match = re.search(r'([-]?\d+[.,]?\d*)', valor)
                            if num_match:
                                num = float(num_match.group(1).replace(',', '.'))
                                valors[label] = num
                                write_log(f"   ✅ {label}: {num}")
                
                # Retornar els valors trobats
                if valors:
                    return {
                        'data': today,
                        'estacio': station_code,
                        'nom_estacio': station_name,
                        'temp_mitjana': valors.get('Temperatura mitjana'),
                        'temp_maxima': valors.get('Temperatura máxima'),
                        'temp_minima': valors.get('Temperatura mínima'),
                        'pluja_acumulada': valors.get('Precipitació acumulada')
                    }
        
        # Si no trobem la taula, provem amb una cerca més agressiva
        write_log("⚠️ No s'ha trobat la taula amb el patró esperat, provant cerca alternativa...")
        
        # Cerca per tots els texts que continguin números i paraules clau
        all_text = soup.get_text()
        import re
        
        # Patrons per a temperatures
        temp_max_pattern = r'Temperatura máxima[:\s]*([-]?\d+[.,]?\d*)'
        temp_min_pattern = r'Temperatura mínima[:\s]*([-]?\d+[.,]?\d*)'
        pluja_pattern = r'Precipitació acumulada[:\s]*([-]?\d+[.,]?\d*)'
        
        temp_max_match = re.search(temp_max_pattern, all_text)
        temp_min_match = re.search(temp_min_pattern, all_text)
        pluja_match = re.search(pluja_pattern, all_text)
        
        resultat = {
            'data': today,
            'estacio': station_code,
            'nom_estacio': station_name,
            'temp_maxima': float(temp_max_match.group(1).replace(',', '.')) if temp_max_match else None,
            'temp_minima': float(temp_min_match.group(1).replace(',', '.')) if temp_min_match else None,
            'pluja_acumulada': float(pluja_match.group(1).replace(',', '.')) if pluja_match else None
        }
        
        if resultat['temp_maxima']:
            write_log(f"   ✅ Temperatura máxima (alternativa): {resultat['temp_maxima']}")
        if resultat['temp_minima']:
            write_log(f"   ✅ Temperatura mínima (alternativa): {resultat['temp_minima']}")
        if resultat['pluja_acumulada'] is not None:
            write_log(f"   ✅ Precipitació acumulada (alternativa): {resultat['pluja_acumulada']}")
        
        return resultat
        
    except Exception as e:
        write_log(f"❌ Error consultant resum diari: {e}")
        return None

def save_daily_summary(summary_data):
    """Guarda el resum diari a daily_summary.json"""
    try:
        # Llegir dades existents
        if os.path.exists('daily_summary.json'):
            with open('daily_summary.json', 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        else:
            all_data = {}
        
        # Actualitzar amb les dades noves
        data_key = summary_data['data']
        
        if data_key not in all_data:
            all_data[data_key] = {}
        
        station_code = summary_data['estacio']
        all_data[data_key][station_code] = {
            'station_name': summary_data['nom_estacio'],
            'temp_maxima': summary_data['temp_maxima'],
            'temp_minima': summary_data['temp_minima'],
            'pluja_acumulada': summary_data['pluja_acumulada'],
            'actualitzat': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Guardar
        with open('daily_summary.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        write_log(f"💾 Resum diari guardat a daily_summary.json")
        return True
        
    except Exception as e:
        write_log(f"❌ Error guardant resum diari: {e}")
        return False

def generar_rss_diari():
    write_log("\n🚀 GENERANT RSS DIARI (RESUMS REALS)")
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    data_avui = now.strftime('%Y-%m-%d')
    
    estacions = [
        {"code": "XJ", "name": "Girona"},
        {"code": "UO", "name": "Fornells de la Selva"}
    ]
    
    entrades = []
    resums_trobats = []
    
    for station in estacions:
        write_log(f"\n📊 Consultant resum REAL per {station['name']}")
        
        # Obtenir resum REAL de MeteoCat
        resum = get_daily_summary_from_meteocat(station['code'], station['name'])
        
        if resum and resum.get('temp_maxima') is not None:
            # Guardar a daily_summary.json
            save_daily_summary(resum)
            resums_trobats.append(resum)
            
            # Preparar dades per RSS
            temp_max = resum['temp_maxima']
            temp_min = resum['temp_minima']
            pluja = resum['pluja_acumulada'] if resum['pluja_acumulada'] is not None else 0.0
            
            # VERSIÓ CATALÀ - RESUM DIARI REAL
            titol_cat = f"📊 RESUM DEL DIA {station['name']} | Data: {data_avui} | Període: 00:00-24:00 | 🔥 Temperatura Màxima: {temp_max}°C | ❄️ Temperatura Mínima: {temp_min}°C | 🌧️ Pluja Acumulada: {pluja}mm"
            
            # VERSIÓ ANGLÈS - RESUM DIARI REAL
            titol_en = f"📊 TODAY'S SUMMARY {station['name']} | Date: {data_avui} | Period: 00:00-24:00 | 🔥 Maximum Temperature: {temp_max}°C | ❄️ Minimum Temperature: {temp_min}°C | 🌧️ Accumulated Rain: {pluja}mm"
            
            titol = f"{titol_cat} || {titol_en}"
            
            # URL per al resum diari
            link_resum = f"https://www.meteo.cat/observacions/xema/dades?codi={station['code']}&dia={data_avui}"
            
            entrada = f'''  <item>
    <title>{titol}</title>
    <link>{link_resum}</link>
    <description>Resum diari de {station['name']} - Data: {data_avui} - Actualitzat a les {now.strftime('%H:%M')} CET / Daily summary from {station['name']} - Date: {data_avui} - Updated at {now.strftime('%H:%M')} CET</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>'''
            
            entrades.append(entrada)
            write_log(f"✅ Resum REAL generat: Màx={temp_max}°C, Mín={temp_min}°C, Pluja={pluja}mm")
        else:
            write_log(f"⚠️ No s'han pogut obtenir dades del dia per {station['name']}")
            
            # Fallback: llegir del daily_summary.json si existeix
            if os.path.exists('daily_summary.json'):
                try:
                    with open('daily_summary.json', 'r', encoding='utf-8') as f:
                        all_data = json.load(f)
                    
                    if data_avui in all_data and station['code'] in all_data[data_avui]:
                        dades = all_data[data_avui][station['code']]
                        
                        titol_cat = f"📊 RESUM DEL DIA {station['name']} | Data: {data_avui} | 🔥 Temperatura Màxima: {dades['temp_maxima']}°C | ❄️ Temperatura Mínima: {dades['temp_minima']}°C | 🌧️ Pluja Acumulada: {dades['pluja_acumulada']}mm"
                        titol_en = f"📊 TODAY'S SUMMARY {station['name']} | Date: {data_avui} | 🔥 Maximum Temperature: {dades['temp_maxima']}°C | ❄️ Minimum Temperature: {dades['temp_minima']}°C | 🌧️ Accumulated Rain: {dades['pluja_acumulada']}mm"
                        titol = f"{titol_cat} || {titol_en}"
                        
                        link_resum = f"https://www.meteo.cat/observacions/xema/dades?codi={station['code']}&dia={data_avui}"
                        
                        entrada = f'''  <item>
    <title>{titol}</title>
    <link>{link_resum}</link>
    <description>Resum diari de {station['name']} - Data: {data_avui} - Actualitzat a les {dades['actualitzat']} CET / Daily summary from {station['name']} - Date: {data_avui} - Updated at {dades['actualitzat']} CET</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>'''
                        
                        entrades.append(entrada)
                        write_log(f"✅ Resum de còpia de seguretat generat")
                except Exception as e:
                    write_log(f"⚠️ Error llegint còpia de seguretat: {e}")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Resums Diaris Reals</title>
  <link>https://www.meteo.cat</link>
  <description>Resums meteorològics reals del dia actual - Estacions Girona i Fornells de la Selva / Today's real weather summaries - Girona and Fornells de la Selva stations</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
{chr(10).join(entrades)}
</channel>
</rss>'''
    
    try:
        with open('update_meteo_dayly.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        write_log("✅ RSS diari (resums reals) generat correctament")
        write_log(f"📁 Arxiu: update_meteo_dayly.rss")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant RSS diari: {e}")
        return False

if __name__ == "__main__":
    with open('debug_dayly.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI RSS DIARI: {datetime.now()} ===\n")
    
    write_log("🚀 Script de resums diaris reals")
    
    try:
        exit = generar_rss_diari()
        if exit:
            write_log("🎉 Èxit complet - RSS diari amb dades reals generat")
        else:
            write_log("💤 Fallada en la generació del RSS diari")
    except Exception as e:
        write_log(f"💥 ERROR: {e}")
        import traceback
        write_log(f"📋 Traceback: {traceback.format_exc()}")
        exit = False
    
    write_log(f"=== FI RSS DIARI: {datetime.now()} ===")
