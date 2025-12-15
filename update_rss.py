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
    with open('debug.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def get_meteo_data(station_code, station_name):
    """Obté les dades del període més recent d'una estació"""
    try:
        write_log(f"🌐 Consultant {station_name} [{station_code}]...")
        url = f"https://www.meteo.cat/observacions/xema/dades?codi={station_code}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'tblperiode'})
        
        if not table:
            write_log("❌ No s'ha trobat la taula")
            return None
            
        rows = table.find_all('tr')
        write_log(f"📊 {len(rows)} files trobades")
        
        # Busquem des del FINAL (dades més recents)
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all(['td', 'th'])
            
            if len(cells) < 3:
                continue
                
            periode = cells[0].get_text(strip=True)
            
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                tm = cells[1].get_text(strip=True)
                if tm and tm not in ['(s/d)', '-', '']:
                    write_log(f"✅ Dades RECENTS trobades: {periode}")
                    
                    # Extracció de dades ADAPTATIVA
                    dades_extretes = {
                        'station_name': station_name,
                        'station_code': station_code,
                        'periode': ajustar_periode(periode),
                        'tm': convertir_a_numero(cells[1].get_text(strip=True)) if len(cells) > 1 else None,
                        'tx': convertir_a_numero(cells[2].get_text(strip=True)) if len(cells) > 2 else None,
                        'tn': convertir_a_numero(cells[3].get_text(strip=True)) if len(cells) > 3 else None,
                        'hr': convertir_a_numero(cells[4].get_text(strip=True)) if len(cells) > 4 else None,
                        'ppt': convertir_a_numero(cells[5].get_text(strip=True)) if len(cells) > 5 else None,
                        'vvm': convertir_a_numero(cells[6].get_text(strip=True)) if len(cells) > 6 else None,
                        'dvm': convertir_a_numero(cells[7].get_text(strip=True)) if len(cells) > 7 else None,
                        'vvx': convertir_a_numero(cells[8].get_text(strip=True)) if len(cells) > 8 else None,
                        'pm': convertir_a_numero(cells[9].get_text(strip=True)) if len(cells) > 9 else None,
                        'rs': convertir_a_numero(cells[10].get_text(strip=True)) if len(cells) > 10 else None
                    }
                    
                    # Netegem les dades que no existeixen (valor None)
                    dades_finales = {k: v for k, v in dades_extretes.items() if v is not None}
                    
                    write_log("📊 Dades extretes:")
                    for key, value in dades_finales.items():
                        if key not in ['station_name', 'station_code', 'periode']:
                            write_log(f"   {key}: {value}")
                    
                    return dades_finales
        
        write_log("❌ No s'han trobat dades vàlides")
        return None
        
    except Exception as e:
        write_log(f"❌ Error consultant dades: {e}")
        return None

def convertir_a_numero(text, default=None):
    """Converteix text a número, retorna None si no és vàlid"""
    if not text or text in ['(s/d)', '-', '']:
        return None
    try:
        return float(text.replace(',', '.'))
    except:
        return None

def ajustar_periode(periode_str):
    """Ajusta l'hora del període segons CET/CEST"""
    try:
        match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', periode_str)
        if match:
            hora_inici = int(match.group(1))
            minut_inici = int(match.group(2))
            hora_fi = int(match.group(3))
            minut_fi = int(match.group(4))
            
            cet = pytz.timezone('CET')
            now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            now_cet = now_utc.astimezone(cet)
            
            is_dst = now_cet.dst() != timedelta(0)
            offset_hours = 2 if is_dst else 1
            
            start_adj = (hora_inici + offset_hours) % 24
            end_adj = (hora_fi + offset_hours) % 24
            
            return f"{start_adj:02d}:{minut_inici:02d}-{end_adj:02d}:{minut_fi:02d}"
            
    except Exception as e:
        write_log(f"⚠️ Error ajustant període: {e}")
    
    return periode_str

def llegir_dades_guardades():
    """Llegeix les dades guardades de totes les estacions (període)"""
    try:
        if os.path.exists('weather_data.json'):
            with open('weather_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        write_log(f"⚠️ Error llegint dades guardades: {e}")
        return {}

def guardar_dades(dades_estacions):
    """Guarda les dades de totes les estacions (període) - SENSE RESUM_DIA"""
    try:
        # Netejar qualsevol 'resum_dia' que pugui haver
        for station_code in dades_estacions:
            if 'resum_dia' in dades_estacions[station_code]:
                del dades_estacions[station_code]['resum_dia']
        
        with open('weather_data.json', 'w', encoding='utf-8') as f:
            json.dump(dades_estacions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_log(f"⚠️ Error guardant dades: {e}")

def generar_rss():
    """Funció principal que genera el RSS amb 4 ítems"""
    write_log("\n🚀 INICIANT GENERACIÓ RSS (DADES PERIODE ACTUAL)")
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    
    # Llegim les dades guardades de períodes anteriors (per a fallback)
    dades_estacions = llegir_dades_guardades()
    write_log(f"📚 Dades guardades (per fallback): {list(dades_estacions.keys())}")
    
    # Definim les estacions
    estacions = [
        {"code": "XJ", "name": "Girona"},
        {"code": "UO", "name": "Fornells de la Selva"}
    ]
    
    dades_actualitzades = {}
    
    # 1️⃣ OBTENIR DADES DEL PERÍODE RECENT (SENSE ACUMULACIÓ)
    for station in estacions:
        write_log(f"\n🎯 [PERÍODE] Consultant {station['name']} [{station['code']}]")
        dades = get_meteo_data(station['code'], station['name'])
        
        if dades:
            dades_actualitzades[station['code']] = dades
            write_log(f"✅ {station['name']} - dades del període actualitzades")
        else:
            # Fallback: dades antigues
            if station['code'] in dades_estacions:
                dades_actualitzades[station['code']] = dades_estacions[station['code']]
                write_log(f"⚠️ {station['name']} - mantenint dades antigues del període")
            else:
                write_log(f"❌ {station['name']} - sense dades del període")
                dades_actualitzades[station['code']] = {
                    'station_name': station['name'],
                    'station_code': station['code'],
                    'periode': '--:--',
                    'tm': None, 'tx': None, 'tn': None, 'hr': None, 'ppt': None
                }
    
    # Guardem les dades del període per a possibles fallbacks futurs
    guardar_dades(dades_actualitzades)
    
    # 2️⃣ GENERAR ELS 2 ÍTEMS RSS (NOMÉS PERIODE ACTUAL)
    write_log(f"\n📝 Generant ítems del període recent...")
    entrades = []
    
    for station_code, dades in dades_actualitzades.items():
        # Formatejar valors del període (evitar None)
        tm_periode = dades.get('tm', 'N/D')
        tx_periode = dades.get('tx', 'N/D')
        tn_periode = dades.get('tn', 'N/D')
        ppt_periode = dades.get('ppt', 'N/D')
        
        # VERSIÓ CATALÀ - PERÍODE RECENT
        parts_cat = [
            f"🌤️ {dades['station_name']}",
            f"Actualitzat: {now.strftime('%H:%M')}",
            f"Període: {dades.get('periode', '--:--')}",
            f"Temp. Actual: {tm_periode}°C" if tm_periode != 'N/D' else "Temp. Actual: N/D",
            f"Màx. Període: {tx_periode}°C" if tx_periode != 'N/D' else "Màx. Període: N/D",
            f"Mín. Període: {tn_periode}°C" if tn_periode != 'N/D' else "Mín. Període: N/D",
            f"💧 Pluja Periode: {ppt_periode}mm" if ppt_periode != 'N/D' else "💧 Pluja Periode: N/D"
        ]
        
        # Dades addicionals
        for key, label in [('vvm', 'Vent'), ('dvm', 'Dir.Vent'), ('vvx', 'Vent Màx'), 
                          ('pm', 'Pressió'), ('rs', 'Radiació')]:
            if key in dades and dades[key] is not None:
                parts_cat.append(f"{label}: {dades[key]}{'km/h' if key in ['vvm', 'vvx'] else '°' if key == 'dvm' else 'hPa' if key == 'pm' else 'W/m²'}")
        
        titol_cat = " | ".join([p for p in parts_cat if p])
        
        # VERSIÓ ANGLÈS - PERÍODE RECENT
        parts_en = [
            f"🌤️ {dades['station_name']}",
            f"Updated: {now.strftime('%H:%M')}",
            f"Period: {dades.get('periode', '--:--')}",
            f"Avg Temp: {tm_periode}°C" if tm_periode != 'N/D' else "Avg Temp: N/D",
            f"Max Period: {tx_periode}°C" if tx_periode != 'N/D' else "Max Period: N/D",
            f"Min Period: {tn_periode}°C" if tn_periode != 'N/D' else "Min Period: N/D",
            f"💧 Period Rain: {ppt_periode}mm" if ppt_periode != 'N/D' else "💧 Period Rain: N/D"
        ]
        
        # Dades addicionals
        for key, label in [('vvm', 'Wind'), ('dvm', 'Wind Dir'), ('vvx', 'Max Wind'), 
                          ('pm', 'Pressure'), ('rs', 'Radiation')]:
            if key in dades and dades[key] is not None:
                parts_en.append(f"{label}: {dades[key]}{'km/h' if key in ['vvm', 'vvx'] else '°' if key == 'dvm' else 'hPa' if key == 'pm' else 'W/m²'}")
        
        titol_en = " | ".join([p for p in parts_en if p])
        titol = f"{titol_cat} || {titol_en}"
        
        # URL per al període recent
        link_periode = f"https://www.meteo.cat/observacions/xema/dades?codi={dades['station_code']}"
        
        entrada = f'''  <item>
    <title>{titol}</title>
    <link>{link_periode}</link>
    <description>Dades meteorològiques de {dades['station_name']} - Període recent - Actualitzat el {now.strftime("%d/%m/%Y a les %H:%M")} CET / Weather data from {dades['station_name']} - Recent period - Updated on {now.strftime("%d/%m/%Y at %H:%M")} CET</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>'''
        
        entrades.append(entrada)
    
    write_log(f"✅ Total ítems generats: {len(entrades)} (2 període)")
    
    # 3️⃣ GENERAR EL FITXER RSS FINAL
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Weather Stations - Temps Real</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estacions Girona i Fornells de la Selva / Real-time weather data - Girona and Fornells de la Selva stations</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
{chr(10).join(entrades)}
</channel>
</rss>'''
    
    try:
        # Generem l'arxiu RSS final
        with open('update_meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        write_log("✅ RSS generat correctament (només període actual)")
        write_log(f"📁 Arxiu: update_meteo.rss")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant RSS: {e}")
        return False

if __name__ == "__main__":
    with open('debug.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI: {datetime.now()} ===\n")
    
    write_log("🚀 Script de dades del període actual")
    
    try:
        exit = generar_rss()
        if exit:
            write_log("🎉 Èxit complet - RSS generat")
        else:
            write_log("💤 Fallada en la generació del RSS")
    except Exception as e:
        write_log(f"💥 ERROR: {e}")
        import traceback
        write_log(f"📋 Traceback: {traceback.format_exc()}")
        exit = False
    
    write_log(f"🏁 Fi del procés: {datetime.now()}")
    sys.exit(0 if exit else 1)
