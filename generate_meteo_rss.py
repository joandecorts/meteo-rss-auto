#!/usr/bin/env python3
# generate_meteo_rss.py - VERSIÓ DEFINITIVA CORREGIDA (Llegendes completes)
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

def scrape_meteocat_data(url, station_name):
    """Extreu TOTES les dades disponibles de cada estació - VERSIÓ SIMPLIFICADA"""
    try:
        write_log(f"🌐 Connectant a {station_name}...")
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
                    write_log(f"🔍 Columnes disponibles: {len(cells)}")
                    
                    # Extracció de dades ADAPTATIVA - només les columnes que existeixen
                    dades_extretes = {
                        'station_name': station_name,
                        'station_code': url.split('codi=')[1][:2] if 'codi=' in url else '',
                        'periode': periode,
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
                            write_log(f"   • {key}: {value}")
                    
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

def convertir_hora_tu_a_local(hora_tu_str):
    """Converteix hora TU (UTC) a hora local (CET = UTC+1) - VERSIÓ MILLORADA"""
    if not hora_tu_str:
        return hora_tu_str
    
    try:
        # Netejar
        hora_tu_str = re.sub(r'\s+', ' ', hora_tu_str.strip())
        
        # Trobar separador
        separador = '-' if '-' in hora_tu_str else '–' if '–' in hora_tu_str else None
        if not separador:
            return hora_tu_str
        
        parts = hora_tu_str.split(separador)
        if len(parts) != 2:
            return hora_tu_str
        
        def convertir_hora(hora):
            hora = hora.strip()
            if ':' in hora:
                try:
                    h_str, m_part = hora.split(':', 1)
                    # Agafar només els dos primers dígits dels minuts
                    m_str = m_part[:2] if len(m_part) >= 2 else '00'
                    
                    h = int(h_str)
                    m = int(m_str) if m_str.isdigit() else 0
                    
                    # Sumar 1 hora per CET (UTC+1)
                    h_local = h + 1
                    if h_local >= 24:
                        h_local -= 24
                    
                    return f"{h_local:02d}:{m:02d}"
                except:
                    return hora
            return hora
        
        inicio = convertir_hora(parts[0])
        fin = convertir_hora(parts[1])
        
        resultat = f"{inicio} - {fin}"
        return resultat
    
    except Exception as e:
        write_log(f"⚠️  Error conversió hora: {e}")
        return hora_tu_str

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

def create_rss_feed():
    """Crea l'arxiu RSS amb totes les dades - VERSIÓ CORREGIDA (Llegendes completes)"""
    
    write_log("\n🚀 GENERADOR RSS METEOCAT - DEFINITIU")
    write_log("=" * 60)
    
    stations = [
        {
            'name': 'Fornells de la Selva',
            'code': 'UO',
            'url': 'https://www.meteo.cat/observacions/xema/dades?codi=UO'
        },
        {
            'name': 'Girona', 
            'code': 'XJ',
            'url': 'https://www.meteo.cat/observacions/xema/dades?codi=XJ'
        },   
        {
            'name': 'Observatori Fabra',
            'code': 'D5',
            'url': 'https://www.meteo.cat/observacions/xema/dades?codi=D5'
        },
        {
            'name': 'Banyoles', 
            'code': 'DJ',
            'url': 'https://www.meteo.cat/observacions/xema/dades?codi=DJ'
        }
    ]
    
    # 🕐 CORRECCIÓ DEFINITIVA: Utilitzar UTC per a les dates del RSS
    # Això evita problemes amb futurs temps a GitHub Actions
    utc_now = datetime.now(pytz.utc)
    # Hora per mostrar al text (hora local d'Espanya)
    display_tz = pytz.timezone('Europe/Madrid')
    display_time = utc_now.astimezone(display_tz)
    # --------------------------------------------------------
    
    # Llegim les dades guardades de totes les estacions
    dades_estacions = llegir_dades_guardades()
    write_log(f"📚 Dades guardades: {list(dades_estacions.keys())}")
    
    dades_actualitzades = {}
    
    for station in stations:
        write_log(f"\n{'='*60}")
        write_log(f"📡 Processant: {station['name']} [{station['code']}]")
        
        dades = scrape_meteocat_data(station['url'], station['name'])
        
        if dades:
            # Convertir hora TU a local
            if 'periode' in dades:
                dades['periode'] = convertir_hora_tu_a_local(dades['periode'])
            
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
        # ✅ VERSIÓ CATALÀ - TEXT COMPLET (sense abreviatures)
        parts_cat = [
            f"🌤️ {dades['station_name']}",
            f"Actualitzat: {display_time.strftime('%H:%M')}",
            f"Període: {dades.get('periode', 'N/D')}",
            f"🌡️ Temp. Mitjana: {dades['tm']}°C",
            f"🔥 Temp. Màxima: {dades['tx']}°C", 
            f"❄️ Temp. Mínima: {dades['tn']}°C",
            f"💧 Humitat: {dades['hr']}%",
            f"🌧️ Precipitació: {dades['ppt']}mm"
        ]
        
        # Afegim dades de vent SOLAMENT si existeixen
        if 'vvm' in dades and dades['vvm'] is not None:
            parts_cat.append(f"💨 Vent: {dades['vvm']}km/h")
            
        if 'dvm' in dades and dades['dvm'] is not None:
            parts_cat.append(f"🧭 Dir.Vent: {dades['dvm']}°")
            
        if 'vvx' in dades and dades['vvx'] is not None:
            parts_cat.append(f"💨 Vent Màx: {dades['vvx']}km/h")
        
        # Afegim pressió SOLAMENT si existeix
        if 'pm' in dades and dades['pm'] is not None:
            parts_cat.append(f"📊 Pressió: {dades['pm']}hPa")
        
        # Afegim radiació solar SOLAMENT si existeix
        if 'rs' in dades and dades['rs'] is not None:
            parts_cat.append(f"☀️ Radiació: {dades['rs']}W/m²")
        
        titol_cat = " | ".join(parts_cat)
        
        # ✅ VERSIÓ ANGLÈS - TEXT COMPLET
        parts_en = [
            f"🌤️ {dades['station_name']}",
            f"Updated: {display_time.strftime('%H:%M')}",
            f"Period: {dades.get('periode', 'N/D')}",
            f"🌡️ Avg Temp: {dades['tm']}°C",
            f"🔥 Max Temp: {dades['tx']}°C", 
            f"❄️ Min Temp: {dades['tn']}°C",
            f"💧 Humidity: {dades['hr']}%",
            f"🌧️ Precipitation: {dades['ppt']}mm"
        ]
        
        # Afegim dades de vent SOLAMENT si existeixen
        if 'vvm' in dades and dades['vvm'] is not None:
            parts_en.append(f"💨 Wind: {dades['vvm']}km/h")
            
        if 'dvm' in dades and dades['dvm'] is not None:
            parts_en.append(f"🧭 Wind Dir: {dades['dvm']}°")
            
        if 'vvx' in dades and dades['vvx'] is not None:
            parts_en.append(f"💨 Max Wind: {dades['vvx']}km/h")
        
        # Afegim pressió SOLAMENT si existeix
        if 'pm' in dades and dades['pm'] is not None:
            parts_en.append(f"📊 Pressure: {dades['pm']}hPa")
        
        # Afegim radiació solar SOLAMENT si existeix
        if 'rs' in dades and dades['rs'] is not None:
            parts_en.append(f"☀️ Radiation: {dades['rs']}W/m²")
        
        titol_en = " | ".join(parts_en)
        
        # ✅ COMBINEM LES DUES VERSIONS (separador més net)
        titol = f"{titol_cat} || {titol_en}"
        
        entrada = f'''  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat/observacions/xema/dades?codi={dades.get('station_code', station_code)}</link>
    <description>Dades meteorològiques de {dades['station_name']} / Weather data from {dades['station_name']} - Actualitzat el {display_time.strftime("%d/%m/%Y a les %H:%M")} / Updated on {display_time.strftime("%d/%m/%Y at %H:%M")}</description>
    <pubDate>{utc_now.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
  </item>'''
        
        entrades.append(entrada)
        write_log(f"✅ Afegida al RSS: {dades['station_name']}")
    
    write_log(f"\n📊 Entrades RSS generades: {len(entrades)}")
    
    # Crear contingut RSS
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Dades Meteo Locals Completes</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estacions Girona / Real-time weather data - Girona station</description>
  <lastBuildDate>{utc_now.strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
{chr(10).join(entrades)}
</channel>
</rss>'''
    
    # Guardar RSS
    try:
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        print(f"\n{'='*60}")
        print(f"✅ RSS generat amb {len(entrades)} estacions")
        print(f"🕐 UTC: {utc_now.strftime('%H:%M:%S')} | Local (CAT): {display_time.strftime('%H:%M:%S')}")
        
        # Mostrar resum
        for station_code, dades in dades_actualitzades.items():
            print(f"   • {dades['station_name']}: {len([k for k in dades.keys() if k not in ['station_name', 'station_code', 'periode']])} dades | {dades.get('periode', 'N/D')}")
        
        # Mostrar contingut del RSS
        print(f"\n📄 CONTINGUT meteo.rss:")
        print("-" * 60)
        # Mostrar només la capçalera i el primer item per no saturar
        lines = rss_content.split('\n')
        for i, line in enumerate(lines[:20]):
            if line.strip():
                print(line[:120])
        print("... [més contingut] ...")
        print("-" * 60)
        
        return True
        
    except Exception as e:
        write_log(f"❌ Error guardant RSS: {e}")
        return False

def setup_automatic_update():
    """Configura l'actualització automàtica cada 5 minuts (per Windows Task Scheduler)"""
    print("\n📋 PER CONFIGURAR L'ACTUALITZACIÓ AUTOMÀTICA CADA 5 MINUTS:")
    print("=" * 60)
    print("1. Obre 'Programador de tasques' (Task Scheduler)")
    print("2. Crea una tasca nova")
    print("3. A la pestanya 'Accions', afegeix:")
    print("   • Programa/Script: python.exe")
    print("   • Arguments: " + os.path.abspath(__file__))
    print("   • Inici a: " + os.path.dirname(os.path.abspath(__file__)))
    print("4. A la pestanya 'Disparadors', afegeix:")
    print("   • Iniciar la tasca: En l'inici")
    print("   • Repetir cada: 5 minuts")
    print("   • Durada: Infinit")
    print("5. A la pestanya 'Condicions', desmarca:")
    print("   • 'Iniciar només si l'ordinador està alimentat per CA'")
    print("   • 'Aturar si canvia a alimentació per bateria'")
    print("=" * 60)

if __name__ == "__main__":
    # Netejar log anterior
    with open('debug.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI: {datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} ===\n")
    
    try:
        exit_code = create_rss_feed()
        
        if exit_code:
            print("\n✅ COMPLETAT AMB ÈXIT")
            print("🔥 Executa: python meteo-server.py")
            print("🌐 Obre: http://localhost:8000/meteo-ticker.html")
            
            # Mostrar opció per configurar actualització automàtica
            setup_automatic_update()
        else:
            print("\n⚠️  COMPLETAT AMB DADES DE PROVA")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        exit_code = False
    
    sys.exit(0 if exit_code else 1)
