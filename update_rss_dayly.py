import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys
import os
import json

def write_log(message):
    """Escriu un missatge al log i també el mostra per pantalla"""
    print(message)
    with open('debug_dayly.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def convertir_a_numero(text):
    """Converteix text a número, retorna None si no és vàlid"""
    if not text:
        return None
    
    text = str(text).strip()
    invalid_values = ['(s/d)', '-', '', 'n/d', '--', 'nan', 'null', 'none']
    if text.lower() in [v.lower() for v in invalid_values]:
        return None
    
    try:
        cleaned = re.sub(r'[^\d.\-]', '', text.replace(',', '.'))
        if cleaned and re.search(r'\d', cleaned):
            value = float(cleaned)
            return value
        else:
            return None
    except Exception as e:
        write_log(f"⚠️ Error convertint número '{text}': {e}")
        return None

def get_daily_summary(station_code, station_name):
    """Obté el resum diari (màximes, mínimes, acumulats) del dia actual"""
    try:
        # URL amb la data d'avui
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://www.meteo.cat/observacions/xema/dades?codi={station_code}&dia={today}"

        write_log(f"🌐 Consultant resum diari {station_name} [{station_code}]...")
        write_log(f"📄 URL: {url}")

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        daily_data = {
            'station_name': station_name,
            'station_code': station_code,
            'data_consulta': today,
            'hora_consulta': datetime.now().strftime('%H:%M'),
            'periode': '00:00-24:00'
        }

        # ESTRATÈGIA 1: Cerca per l'ID 'resum-diari' o per l'etiqueta h2
        write_log("🔍 Cercant resum diari...")
        resum_div = soup.find('div', id='resum-diari')
        
        if not resum_div:
            h2_title = soup.find('h2', string=re.compile('Resum diari', re.IGNORECASE))
            if h2_title:
                resum_div = h2_title.find_parent('div')
                if resum_div:
                    write_log("✅ Trobat 'Resum diari' via h2.")

        if resum_div:
            write_log("✅ Secció del resum diari localitzada.")
            # Busquem el text complet del resum
            full_resum_text = resum_div.get_text()
            write_log(f"📄 Text del resum: {full_resum_text[:500]}...")  # Primeres 500 lletres per debug

            # Patrons regex per extreure dades del text
            patterns = {
                'tm': r'temperatura\s+mitjana[^\d]*([\d,\.]+)',
                'tx': r'temperatura\s+(?:màxima|máxima)[^\d]*([\d,\.]+)',
                'tn': r'temperatura\s+mínima[^\d]*([\d,\.]+)',
                'hr': r'humitat\s+(?:relativa\s+)?mitjana[^\d]*([\d,\.]+)',
                'ppt': r'precipitaci[oó]\s+(?:acumulada\s+)?[^\d]*([\d,\.]+)'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, full_resum_text, re.IGNORECASE)
                if match:
                    value = match.group(1).replace(',', '.')
                    daily_data[key] = convertir_a_numero(value)
                    write_log(f"   ✅ {key.upper()} (via regex): {daily_data[key]}")
                else:
                    write_log(f"   ❌ {key.upper()} NO trobat amb patró.")
        else:
            write_log("❌ No s'ha trobat cap contenidor del resum diari.")

        # COMPROVACIÓ FINAL: Tenim alguna dada vàlida?
        dades_valides = any(daily_data.get(key) is not None for key in ['tm', 'tx', 'tn', 'hr', 'ppt'])
        if dades_valides:
            write_log("✅ Dades del resum diari extretes amb èxit.")
            for key, value in daily_data.items():
                if value is not None and key not in ['station_name', 'station_code', 'data_consulta', 'hora_consulta', 'periode']:
                    write_log(f"   📍 {key.upper()}: {value}")
            return daily_data
        else:
            write_log("❌ No s'han pogut extreure dades del resum diari.")
            return None

    except Exception as e:
        write_log(f"❌ Error consultant resum diari: {e}")
        import traceback
        write_log(f"📋 Traceback: {traceback.format_exc()}")
        return None

def generar_rss_daily():
    write_log("\n🚀 INICIANT GENERACIÓ RSS RESUM DIARI")
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    today_str = now.strftime('%Y-%m-%d')
    
    # Determinar si és hora d'estiu (CEST) o hora d'hivern (CET)
    is_dst = now.dst() != timedelta(0)
    timezone_cat = "CEST" if is_dst else "CET"
    timezone_en = "CEST" if is_dst else "CET"
    
    write_log(f"📅 Data actual: {today_str}")
    write_log(f"⏰ Hora actual: {now.strftime('%H:%M')} {timezone_cat}")
    
    # Consultem les DUES estacions per obtenir el resum diari
    estacions = [
        {"code": "XJ", "name": "Girona"},
        {"code": "UO", "name": "Fornells de la Selva"}
    ]
    
    dades_diaries = {}
    
    for station in estacions:
        write_log(f"\n🎯 CONSULTANT RESUM DIARI: {station['name']} [{station['code']}]")
        dades = get_daily_summary(station['code'], station['name'])
        
        if dades:
            dades_diaries[station['code']] = dades
            write_log(f"✅ RESUM DIARI OBTINGUT PER A {station['name']}")
        else:
            write_log(f"⚠️ {station['name']} - NO S'HA POGUT OBTENIR RESUM DIARI")
            dades_diaries[station['code']] = {
                'station_name': station['name'],
                'station_code': station['code'],
                'data_consulta': today_str,
                'hora_consulta': now.strftime('%H:%M'),
                'error': 'Dades no disponibles'
            }
    
    # Generem les entrades RSS per cada estació
    entrades = []
    
    for station_code, dades in dades_diaries.items():
        if 'error' in dades:
            titol_cat = f"⚠️ {dades['station_name']} - Dades diàries no disponibles"
            titol_en = f"⚠️ {dades['station_name']} - Daily data not available"
            titol = f"{titol_cat} || {titol_en}"
            desc_cat = f"Dades del resum diari no disponibles per a {dades['station_name']} - Actualitzat a les {dades['hora_consulta']} {timezone_cat}"
            desc_en = f"Daily summary data not available for {dades['station_name']} - Updated at {dades['hora_consulta']} {timezone_en}"
        else:
            # ✅ VERSIÓ CATALÀ - RESUM DIARI
            parts_cat = [f"📊 RESUM AVUI {dades['station_name']}"]
            
            if dades.get('tx') is not None:
                parts_cat.append(f"T. Màxima: {dades['tx']}°C")
            if dades.get('tn') is not None:
                parts_cat.append(f"T. Mínima: {dades['tn']}°C")
            if dades.get('tm') is not None:
                parts_cat.append(f"T. Mitjana: {dades['tm']}°C")
            if dades.get('ppt') is not None:
                parts_cat.append(f"Pluja: {dades['ppt']}mm")
            if dades.get('hr') is not None:
                parts_cat.append(f"Humitat: {dades['hr']}%")
            
            titol_cat = " | ".join(parts_cat)
            
            # ✅ VERSIÓ ANGLÈS - RESUM DIARI
            parts_en = [f"📊 TODAY'S SUMMARY {dades['station_name']}"]
            
            if dades.get('tx') is not None:
                parts_en.append(f"Max Temp: {dades['tx']}°C")
            if dades.get('tn') is not None:
                parts_en.append(f"Min Temp: {dades['tn']}°C")
            if dades.get('tm') is not None:
                parts_en.append(f"Avg Temp: {dades['tm']}°C")
            if dades.get('ppt') is not None:
                parts_en.append(f"Rain: {dades['ppt']}mm")
            if dades.get('hr') is not None:
                parts_en.append(f"Humidity: {dades['hr']}%")
            
            titol_en = " | ".join(parts_en)
            titol = f"{titol_cat} || {titol_en}"
            
            desc_parts_cat = [f"Resum diari de {dades['station_name']} - Data: {today_str}"]
            if dades.get('tx') is not None:
                desc_parts_cat.append(f"Temperatura màxima: {dades['tx']}°C")
            if dades.get('tn') is not None:
                desc_parts_cat.append(f"Temperatura mínima: {dades['tn']}°C")
            if dades.get('ppt') is not None:
                desc_parts_cat.append(f"Pluja acumulada: {dades['ppt']}mm")
            desc_parts_cat.append(f"Actualitzat a les {dades.get('hora_consulta', now.strftime('%H:%M'))} {timezone_cat}")
            
            desc_parts_en = [f"Daily summary from {dades['station_name']} - Date: {today_str}"]
            if dades.get('tx') is not None:
                desc_parts_en.append(f"Maximum temperature: {dades['tx']}°C")
            if dades.get('tn') is not None:
                desc_parts_en.append(f"Minimum temperature: {dades['tn']}°C")
            if dades.get('ppt') is not None:
                desc_parts_en.append(f"Accumulated rain: {dades['ppt']}mm")
            desc_parts_en.append(f"Updated at {dades.get('hora_consulta', now.strftime('%H:%M'))} {timezone_en}")
            
            desc_cat = " | ".join(desc_parts_cat)
            desc_en = " | ".join(desc_parts_en)
        
        # URL amb la data d'avui
        today_url = f"https://www.meteo.cat/observacions/xema/dades?codi={dades['station_code']}&dia={today_str}"
        pub_date = now.strftime("%a, %d %b %Y %H:%M:%S ") + ("CEST" if is_dst else "CET")
        
        entrada = f'''  <item>
    <title>{titol}</title>
    <link>{today_url}</link>
    <description>{desc_cat} / {desc_en}</description>
    <pubDate>{pub_date}</pubDate>
  </item>'''
        
        entrades.append(entrada)
    
    write_log(f"\n📊 Entrades de resum diari generades: {len(entrades)}")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Resum Diari</title>
  <link>https://www.meteo.cat</link>
  <description>Resums meteorològics del dia actual - Estacions Girona i Fornells de la Selva / Today's weather summaries - Girona and Fornells de la Selva stations</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S ")}{"CEST" if is_dst else "CET"}</lastBuildDate>
{chr(10).join(entrades)}
</channel>
</rss>'''
    
    try:
        with open('meteo_dayly.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        write_log("✅ RSS de resum diari actualitzat correctament")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant RSS de resum: {e}")
        return False

if __name__ == "__main__":
    with open('debug_dayly.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI RESUM DIARI: {datetime.now()} ===\n")
    
    write_log("🚀 Script de resum diari iniciat")
    
    try:
        exit_code = generar_rss_daily()
        if exit_code:
            write_log("\n🎉 ÈXIT COMPLET DEL PROCÉS DE RESUM DIARI")
        else:
            write_log("\n💤 FALLADA EN EL PROCÉS DE RESUM DIARI")
    except Exception as e:
        write_log(f"\n💥 ERROR FATAL: {e}")
        exit_code = False
    
    write_log(f"\n🏁 FI DEL PROCÉS: {datetime.now()}")
    sys.exit(0 if exit_code else 1)
