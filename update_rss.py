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

def get_current_station():
    """Alterna entre estacions basant-se en un fitxer de estat"""
    try:
        estat_file = 'station_state.json'
        
        if os.path.exists(estat_file):
            with open(estat_file, 'r') as f:
                estat = json.load(f)
            ultima_estacio = estat.get('ultima_estacio', 'XJ')
        else:
            ultima_estacio = 'XJ'
        
        # Alternem estacions
        if ultima_estacio == 'XJ':
            nova_estacio = {"code": "UO", "name": "Fornells de la Selva"}
        else:
            nova_estacio = {"code": "XJ", "name": "Girona"}
        
        # Guardem l'estat
        with open(estat_file, 'w') as f:
            json.dump({'ultima_estacio': nova_estacio['code']}, f)
        
        write_log(f"🔄 Alternança: {ultima_estacio} → {nova_estacio['code']}")
        return nova_estacio
        
    except Exception as e:
        write_log(f"❌ Error en alternança: {e}")
        return {"code": "XJ", "name": "Girona"}

def get_meteo_data(station_code, station_name):
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
        
        # ⚠️ CANVI IMPORTANT: Busquem des del FINAL (dades més recents)
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all(['td', 'th'])
            
            if len(cells) < 3:
                continue
                
            periode = cells[0].get_text(strip=True)
            
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                tm = cells[1].get_text(strip=True)
                if tm and tm not in ['(s/d)', '-', '']:
                    write_log(f"✅ Dades RECENTS trobades: {periode}")
                    
                    # Extracció de dades
                    tm = cells[1].get_text(strip=True)
                    tx = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    tn = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    hr = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                    ppt = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                    vvm = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                    dvm = cells[7].get_text(strip=True) if len(cells) > 7 else ''
                    vvx = cells[8].get_text(strip=True) if len(cells) > 8 else ''
                    pm = cells[9].get_text(strip=True) if len(cells) > 9 else ''
                    rs = cells[10].get_text(strip=True) if len(cells) > 10 else ''
                    
                    def a_numero(text, default=0.0):
                        if not text or text in ['(s/d)', '-', '']:
                            return default
                        try:
                            return float(text.replace(',', '.'))
                        except:
                            return default
                    
                    periode_ajustat = ajustar_periode(periode)
                    
                    return {
                        'station_name': station_name,
                        'station_code': station_code,
                        'periode': periode_ajustat,
                        'tm': a_numero(tm),
                        'tx': a_numero(tx),
                        'tn': a_numero(tn),
                        'hr': a_numero(hr),
                        'ppt': a_numero(ppt),
                        'vvm': a_numero(vvm),
                        'dvm': a_numero(dvm),
                        'vvx': a_numero(vvx),
                        'pm': a_numero(pm),
                        'rs': a_numero(rs)
                    }
        
        write_log("❌ No s'han trobat dades vàlides")
        return None
        
    except Exception as e:
        write_log(f"❌ Error consultant dades: {e}")
        return None

def ajustar_periode(periode_str):
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

def generar_rss():
    write_log("\n🚀 INICIANT GENERACIÓ RSS")
    
    station = get_current_station()
    write_log(f"🎯 Estació: {station['name']} [{station['code']}]")
    
    dades = get_meteo_data(station['code'], station['name'])
    
    if not dades:
        write_log("❌ No s'han obtingut dades")
        return False
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    
    # Construïm el títol amb totes les dades
    parts = [
        f"🌤️ {dades['station_name']}",
        f"Actualitzat: {now.strftime('%H:%M')}",
        f"Període: {dades['periode']}",
        f"Temp. Mitjana: {dades['tm']}°C",
        f"Temp. Màxima: {dades['tx']}°C", 
        f"Temp. Mínima: {dades['tn']}°C",
        f"Humitat: {dades['hr']}%",
        f"Precipitació: {dades['ppt']}mm"
    ]
    
    if dades['vvm'] > 0:
        parts.extend([f"Vent: {dades['vvm']}km/h", f"Vent Màx: {dades['vvx']}km/h"])
    
    if dades['pm'] > 0:
        parts.append(f"Pressió: {dades['pm']}hPa")
    
    titol = " | ".join(parts)
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Weather Stations</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estacions Girona i Fornells de la Selva</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat/observacions/xema/dades?codi={dades['station_code']}</link>
    <description>Dades meteorològiques de {dades['station_name']} - Actualitzat el {now.strftime("%d/%m/%Y a les %H:%M")}</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    try:
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        write_log("✅ RSS guardat correctament")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant RSS: {e}")
        return False

if __name__ == "__main__":
    with open('debug.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI: {datetime.now()} ===\n")
    
    write_log("🚀 Script iniciat")
    
    try:
        exit = generar_rss()
        if exit:
            write_log("🎉 Èxit complet")
        else:
            write_log("💤 Fallada")
    except Exception as e:
        write_log(f"💥 ERROR: {e}")
        exit = False
    
    write_log(f"🏁 Fi: {datetime.now()}")
    sys.exit(0 if exit else 1)
