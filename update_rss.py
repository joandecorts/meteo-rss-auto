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
        
        # DEBUG: Mostrem la capçalera per saber quantes columnes té aquesta estació
        if len(rows) > 0:
            header_cells = rows[0].find_all(['td', 'th'])
            write_log(f"🔍 CAPÇALERA - {len(header_cells)} columnes:")
            for i, cell in enumerate(header_cells):
                write_log(f"   Columna {i}: '{cell.get_text(strip=True)}'")
        
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
                    write_log(f"🔍 Columnes disponibles: {len(cells)}")
                    
                    # Extracció de dades COMPLETA - adaptativa a les columnes disponibles
                    # Les columnes estan en aquest ordre:
                    # 0: Període, 1: TM, 2: TX, 3: TN, 4: HRM, 5: PPT, 
                    # 6: VVM, 7: DVM, 8: VVX, 9: PM, 10: RS
                    
                    tm = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    tx = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    tn = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    hr = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                    ppt = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                    vvm = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                    dvm = cells[7].get_text(strip=True) if len(cells) > 7 else ''  # ✅ NOVA COLUMNA
                    vvx = cells[8].get_text(strip=True) if len(cells) > 8 else ''
                    pm = cells[9].get_text(strip=True) if len(cells) > 9 else ''
                    rs = cells[10].get_text(strip=True) if len(cells) > 10 else ''  # ✅ NOVA COLUMNA
                    
                    write_log("📊 Dades extretes:")
                    write_log(f"   TM: '{tm}' | TX: '{tx}' | TN: '{tn}'")
                    write_log(f"   HR: '{hr}' | PPT: '{ppt}'")
                    write_log(f"   VVM: '{vvm}' | DVM: '{dvm}' | VVX: '{vvx}'")
                    write_log(f"   PM: '{pm}' | RS: '{rs}'")
                    
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
                        'dvm': a_numero(dvm),  # ✅ NOVA COLUMNA
                        'vvx': a_numero(vvx),
                        'pm': a_numero(pm),
                        'rs': a_numero(rs)     # ✅ NOVA COLUMNA
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

def llegir_dades_guardades():
    """Llegeix les dades guardades de totes les estacions"""
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
    """Guarda les dades de totes les estacions"""
    try:
        with open('weather_data.json', 'w', encoding='utf-8') as f:
            json.dump(dades_estacions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_log(f"⚠️ Error guardant dades: {e}")

def generar_rss():
    write_log("\n🚀 INICIANT GENERACIÓ RSS")
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    
    # Llegim les dades guardades de totes les estacions
    dades_estacions = llegir_dades_guardades()
    write_log(f"📚 Dades guardades: {list(dades_estacions.keys())}")
    
    # Consultem les DUES estacions cada vegada
    estacions = [
        {"code": "XJ", "name": "Girona"},
        {"code": "UO", "name": "Fornells de la Selva"}
    ]
    
    dades_actualitzades = {}
    
    for station in estacions:
        write_log(f"\n🎯 Consultant {station['name']} [{station['code']}]")
        dades = get_meteo_data(station['code'], station['name'])
        
        if dades:
            dades_actualitzades[station['code']] = dades
            write_log(f"✅ {station['name']} actualitzada")
        else:
            # Si no podem obtenir dades noves, mantenim les antigues
            if station['code'] in dades_estacions:
                dades_actualitzades[station['code']] = dades_estacions[station['code']]
                write_log(f"⚠️ {station['name']} - mantenint dades antigues")
            else:
                write_log(f"❌ {station['name']} - sense dades")
    
    # Actualitzem les dades guardades
    guardar_dades(dades_actualitzades)
    
    # Generem les entrades RSS per cada estació
    entrades = []
    
    for station_code, dades in dades_actualitzades.items():
        # ✅ VERSIÓ CATALÀ
        parts_cat = [
            f"🌤️ {dades['station_name']}",
            f"Actualitzat: {now.strftime('%H:%M')}",
            f"Període: {dades['periode']}",
            f"Temp. Mitjana: {dades['tm']}°C",
            f"Temp. Màxima: {dades['tx']}°C", 
            f"Temp. Mínima: {dades['tn']}°C",
            f"Humitat: {dades['hr']}%",
            f"Precipitació: {dades['ppt']}mm"
        ]
        
        # Afegim dades de vent si estan disponibles
        if dades['vvm'] > 0:
            parts_cat.append(f"Vent: {dades['vvm']}km/h")
            if dades['dvm'] > 0:  # ✅ NOVA: Direcció del vent
                parts_cat.append(f"Dir.Vent: {dades['dvm']}°")
            if dades['vvx'] > 0:
                parts_cat.append(f"Vent Màx: {dades['vvx']}km/h")
        
        # Afegim pressió si està disponible
        if dades['pm'] > 0:
            parts_cat.append(f"Pressió: {dades['pm']}hPa")
        
        # Afegim radiació solar si està disponible ✅ NOVA
        if dades['rs'] > 0:
            parts_cat.append(f"Radiació: {dades['rs']}W/m²")
        
        titol_cat = " | ".join(parts_cat)
        
        # ✅ VERSIÓ ANGLÈS
        parts_en = [
            f"🌤️ {dades['station_name']}",
            f"Updated: {now.strftime('%H:%M')}",
            f"Period: {dades['periode']}",
            f"Avg Temp: {dades['tm']}°C",
            f"Max Temp: {dades['tx']}°C", 
            f"Min Temp: {dades['tn']}°C",
            f"Humidity: {dades['hr']}%",
            f"Precipitation: {dades['ppt']}mm"
        ]
        
        # Afegim dades de vent si estan disponibles
        if dades['vvm'] > 0:
            parts_en.append(f"Wind: {dades['vvm']}km/h")
            if dades['dvm'] > 0:  # ✅ NOVA: Direcció del vent
                parts_en.append(f"Wind Dir: {dades['dvm']}°")
            if dades['vvx'] > 0:
                parts_en.append(f"Max Wind: {dades['vvx']}km/h")
        
        # Afegim pressió si està disponible
        if dades['pm'] > 0:
            parts_en.append(f"Pressure: {dades['pm']}hPa")
        
        # Afegim radiació solar si està disponible ✅ NOVA
        if dades['rs'] > 0:
            parts_en.append(f"Radiation: {dades['rs']}W/m²")
        
        titol_en = " | ".join(parts_en)
        
        # ✅ COMBINEM LES DUES VERSIONS
        titol = f"{titol_cat} || {titol_en}"
        
        entrada = f'''  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat/observacions/xema/dades?codi={dades['station_code']}</link>
    <description>Dades meteorològiques de {dades['station_name']} / Weather data from {dades['station_name']} - Actualitzat el {now.strftime("%d/%m/%Y a les %H:%M")} / Updated on {now.strftime("%d/%m/%Y at %H:%M")}</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>'''
        
        entrades.append(entrada)
    
    write_log(f"📊 Entrades generades: {len(entrades)}")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Weather Stations</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estacions Girona i Fornells de la Selva / Real-time weather data - Girona and Fornells de la Selva stations</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
{chr(10).join(entrades)}
</channel>
</rss>'''
    
    try:
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        write_log("✅ RSS actualitzat correctament")
        write_log(f"🏁 Estacions al RSS: {list(dades_actualitzades.keys())}")
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
