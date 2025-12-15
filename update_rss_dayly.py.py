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

def get_daily_summary(station_code, station_name):
    """Obté el resum diari (màximes, mínimes, acumulats) del dia actual"""
    try:
        # URL amb la data d'avui
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://www.meteo.cat/observacions/xema/dades?codi={station_code}&dia={today}"
        
        write_log(f"🌐 Consultant resum diari {station_name} [{station_code}]...")
        write_log(f"📄 URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ca,es;q=0.8,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Busquem el títol "Resum diari"
        write_log("🔍 Cercant 'Resum diari'...")
        resum_diari_section = None
        
        # Buscar per tots els texts que continguin "Resum diari"
        for element in soup.find_all(['h2', 'h3', 'h4', 'div', 'table']):
            text = element.get_text(strip=True)
            if 'resum diari' in text.lower():
                write_log(f"✅ Títol 'Resum diari' trobat: {text}")
                resum_diari_section = element
                break
        
        # Si no trobem per text, busquem taules amb les dades específiques
        if not resum_diari_section:
            write_log("🔍 Cercant taula amb dades de resum...")
            
            # Buscar totes les taules
            tables = soup.find_all('table')
            for i, table in enumerate(tables):
                table_text = table.get_text(strip=True).lower()
                # Buscar paraules clau del resum
                if any(keyword in table_text for keyword in ['temperatura', 'màxima', 'mínima', 'acumulada', 'humitat']):
                    write_log(f"📋 Taula potencial de resum trobada #{i+1}")
                    resum_diari_section = table
                    break
        
        if not resum_diari_section:
            write_log("❌ No s'ha trobat la secció 'Resum diari'")
            return None
        
        # Ara extraiem les dades de la taula del resum
        write_log("🔍 Extraient dades del resum diari...")
        
        daily_data = {
            'station_name': station_name,
            'station_code': station_code,
            'data_consulta': today,
            'hora_consulta': datetime.now().strftime('%H:%M'),
            'periode': '00:00-24:00'  # Per defecte per al resum diari
        }
        
        # Intentem trobar la taula del resum
        table = resum_diari_section
        if resum_diari_section.name != 'table':
            # Si no és una taula, buscar taules dins de l'element
            table = resum_diari_section.find('table')
        
        if table:
            rows = table.find_all('tr')
            write_log(f"📊 Taula de resum: {len(rows)} files")
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    write_log(f"   Label: {label}, Value: {value}")
                    
                    # Mapejar les etiquetes als nostres camps
                    if 'temperatura mitjana' in label:
                        daily_data['tm'] = convertir_a_numero(value)
                    elif 'temperatura máxima' in label or 'temperatura màxima' in label:
                        daily_data['tx'] = convertir_a_numero(value)
                    elif 'temperatura mínima' in label:
                        daily_data['tn'] = convertir_a_numero(value)
                    elif 'humitat relativa mitjana' in label or 'humitat mitjana' in label:
                        daily_data['hr'] = convertir_a_numero(value)
                    elif 'precipitació acumulada' in label or 'precipitació' in label:
                        daily_data['ppt'] = convertir_a_numero(value)
        
        # Si no hem trobat dades a la taula, intentem buscar per text directament
        if not any(key in daily_data for key in ['tm', 'tx', 'tn', 'hr', 'ppt']):
            write_log("🔍 Buscant dades per text directe a la pàgina...")
            page_text = soup.get_text()
            
            # Buscar patrons específics
            patterns = {
                'tm': r'Temperatura mitjana.*?(\d+\.?\d*)',
                'tx': r'Temperatura máxima.*?(\d+\.?\d*)',
                'tn': r'Temperatura mínima.*?(\d+\.?\d*)',
                'hr': r'Humitat relativa mitjana.*?(\d+\.?\d*)',
                'ppt': r'Precipitació acumulada.*?(\d+\.?\d*)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    daily_data[key] = convertir_a_numero(match.group(1))
                    write_log(f"✅ {key} trobat per regex: {daily_data[key]}")
        
        # Comprovar si tenim dades vàlides
        dades_validas = any(daily_data.get(key) is not None for key in ['tm', 'tx', 'tn', 'hr', 'ppt'])
        
        if dades_validas:
            write_log("📊 Dades del resum diari extretes:")
            for key, value in daily_data.items():
                if value is not None:
                    write_log(f"   {key}: {value}")
            return daily_data
        else:
            write_log("❌ No s'han pogut extreure dades del resum diari")
            return None
        
    except Exception as e:
        write_log(f"❌ Error consultant resum diari: {str(e)[:200]}")
        return None

def convertir_a_numero(text):
    """Converteix text a número, retorna None si no és vàlid"""
    if not text:
        return None
    
    # Netejar el text
    text = str(text).strip()
    
    # Llista de valors no vàlids
    invalid_values = ['(s/d)', '-', '', 'n/d', '--', 'nan', 'null', 'none']
    if text.lower() in [v.lower() for v in invalid_values]:
        return None
    
    try:
        # Eliminar unitats i caràcters no numèrics (deixant punt decimal i signe negatiu)
        cleaned = re.sub(r'[^\d.\-]', '', text.replace(',', '.'))
        
        # Comprovar si queda algun número
        if cleaned and re.search(r'\d', cleaned):
            # Convertir a float
            value = float(cleaned)
            
            # Validacions addicionals per valors meteorològics
            if 'humitat' in str(text).lower() and (value < 0 or value > 100):
                write_log(f"⚠️ Valor de humitat fora de rang: {value}")
                return None
                
            if 'temperatura' in str(text).lower() and (value < -50 or value > 50):
                write_log(f"⚠️ Valor de temperatura fora de rang: {value}")
                return None
                
            if 'precipitació' in str(text).lower() and value < 0:
                write_log(f"⚠️ Valor de precipitació negatiu: {value}")
                return None
                
            return value
        else:
            return None
    except Exception as e:
        write_log(f"⚠️ Error convertint número '{text}': {e}")
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
        write_log(f"\n{'='*60}")
        write_log(f"🎯 CONSULTANT RESUM DIARI: {station['name']} [{station['code']}]")
        write_log(f"{'='*60}")
        
        dades = get_daily_summary(station['code'], station['name'])
        
        if dades:
            dades_diaries[station['code']] = dades
            write_log(f"✅ RESUM DIARI OBTINGUT PER A {station['name']}")
            
            # Mostrar resum de les dades obtingudes
            if dades.get('tx') is not None:
                write_log(f"   🌡️  Temperatura màxima: {dades['tx']}°C")
            if dades.get('tn') is not None:
                write_log(f"   ❄️  Temperatura mínima: {dades['tn']}°C")
            if dades.get('tm') is not None:
                write_log(f"   📊 Temperatura mitjana: {dades['tm']}°C")
            if dades.get('ppt') is not None:
                write_log(f"   💧 Precipitació acumulada: {dades['ppt']}mm")
            if dades.get('hr') is not None:
                write_log(f"   💦 Humitat mitjana: {dades['hr']}%")
        else:
            write_log(f"⚠️  {station['name']} - NO S'HA POGUT OBTENIR RESUM DIARI")
            # Dades mínimes per mantenir l'estructura
            dades_diaries[station['code']] = {
                'station_name': station['name'],
                'station_code': station['code'],
                'data_consulta': today_str,
                'hora_consulta': now.strftime('%H:%M'),
                'error': 'Dades no disponibles'
            }
    
    write_log(f"\n{'='*60}")
    write_log(f"📊 RESUM FINAL - Estacions amb dades: {len([d for d in dades_diaries.values() if 'error' not in d])}/2")
    write_log(f"{'='*60}")
    
    # Generem les entrades RSS per cada estació
    entrades = []
    
    for station_code, dades in dades_diaries.items():
        if 'error' in dades:
            # Cas d'error - mostrar missatge d'error
            titol_cat = f"⚠️ {dades['station_name']} - Dades diàries no disponibles"
            titol_en = f"⚠️ {dades['station_name']} - Daily data not available"
            titol = f"{titol_cat} || {titol_en}"
            
            desc_cat = f"Dades del resum diari no disponibles per a {dades['station_name']} - Actualitzat a les {dades['hora_consulta']} {timezone_cat}"
            desc_en = f"Daily summary data not available for {dades['station_name']} - Updated at {dades['hora_consulta']} {timezone_en}"
        else:
            # ✅ VERSIÓ CATALÀ - RESUM DIARI
            parts_cat = [
                f"📊 RESUM AVUI {dades['station_name']}",
                f"Actualitzat: {dades.get('hora_consulta', now.strftime('%H:%M'))} {timezone_cat}",
            ]
            
            # Temperatura màxima
            if dades.get('tx') is not None:
                parts_cat.append(f"T. Màxima: {dades['tx']}°C")
            
            # Temperatura mínima
            if dades.get('tn') is not None:
                parts_cat.append(f"T. Mínima: {dades['tn']}°C")
            
            # Temperatura mitjana
            if dades.get('tm') is not None:
                parts_cat.append(f"T. Mitjana: {dades['tm']}°C")
            
            # Precipitació acumulada
            if dades.get('ppt') is not None:
                parts_cat.append(f"Pluja: {dades['ppt']}mm")
            
            # Humitat
            if dades.get('hr') is not None:
                parts_cat.append(f"Humitat: {dades['hr']}%")
            
            titol_cat = " | ".join(parts_cat)
            
            # ✅ VERSIÓ ANGLÈS - RESUM DIARI
            parts_en = [
                f"📊 TODAY'S SUMMARY {dades['station_name']}",
                f"Updated: {dades.get('hora_consulta', now.strftime('%H:%M'))} {timezone_en}",
            ]
            
            # Maximum temperature
            if dades.get('tx') is not None:
                parts_en.append(f"Max Temp: {dades['tx']}°C")
            
            # Minimum temperature
            if dades.get('tn') is not None:
                parts_en.append(f"Min Temp: {dades['tn']}°C")
            
            # Average temperature
            if dades.get('tm') is not None:
                parts_en.append(f"Avg Temp: {dades['tm']}°C")
            
            # Accumulated rain
            if dades.get('ppt') is not None:
                parts_en.append(f"Rain: {dades['ppt']}mm")
            
            # Humidity
            if dades.get('hr') is not None:
                parts_en.append(f"Humidity: {dades['hr']}%")
            
            titol_en = " | ".join(parts_en)
            
            # ✅ COMBINEM LES DUES VERSIONS
            titol = f"{titol_cat} || {titol_en}"
            
            # Descripció per al RSS
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
        
        # Format de data per al RSS
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
        write_log(f"📁 Arxiu: meteo_dayly.rss")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant RSS de resum: {e}")
        return False

if __name__ == "__main__":
    # Netegem el log anterior
    with open('debug_dayly.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI RESUM DIARI: {datetime.now()} ===\n")
        f.write(f"Versió: Captura directa de resum diari de la web\n")
    
    write_log("🚀 Script de resum diari iniciat")
    write_log("🎯 Objectiu: Capturar 'Resum diari' de la pàgina web")
    
    try:
        exit_code = generar_rss_daily()
        if exit_code:
            write_log("\n🎉 ÈXIT COMPLET DEL PROCÉS DE RESUM DIARI")
            write_log(f"💾 Dades guardades a: meteo_dayly.rss")
        else:
            write_log("\n💤 FALLADA EN EL PROCÉS DE RESUM DIARI")
    except Exception as e:
        write_log(f"\n💥 ERROR FATAL: {e}")
        import traceback
        write_log(f"📋 Traceback: {traceback.format_exc()}")
        exit_code = False
    
    write_log(f"\n🏁 FI DEL PROCÉS: {datetime.now()}")
    sys.exit(0 if exit_code else 1)