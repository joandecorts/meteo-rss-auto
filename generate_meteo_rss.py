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
    """Extreu TOTES les dades disponibles de cada estació - VERSIÓ MILLORADA"""
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
        
        if len(rows) < 2:
            write_log("❌ Taula massa curta per tenir dades")
            return None
        
        # Primer, obtenim els noms de les columnes (capçaleres)
        headers_row = rows[0]
        columnes = []
        for cell in headers_row.find_all(['td', 'th']):
            text = cell.get_text(strip=True)
            columnes.append(text)
        
        write_log(f"📋 Columnes detectades ({len(columnes)}):")
        for idx, col in enumerate(columnes):
            write_log(f"   [{idx}] {col}")
        
        # Mapeig MILLORAT de columnes a claus de dades
        columna_mapping = {}
        
        for idx, col_name in enumerate(columnes):
            col_name_lower = col_name.lower()
            
            # Període - sempre és la primera columna
            if idx == 0:
                columna_mapping['periode'] = idx
                continue
            
            # Temperatura TM
            if ('tm' in col_name_lower or 'mitjana' in col_name_lower) and ('°c' in col_name or 'c' in col_name_lower):
                columna_mapping['tm'] = idx
            # Temperatura TX
            elif ('tx' in col_name_lower or 'màxima' in col_name_lower or 'maxima' in col_name_lower) and ('°c' in col_name or 'c' in col_name_lower):
                columna_mapping['tx'] = idx
            # Temperatura TN
            elif ('tn' in col_name_lower or 'mínima' in col_name_lower or 'minima' in col_name_lower) and ('°c' in col_name or 'c' in col_name_lower):
                columna_mapping['tn'] = idx
            # Humitat
            elif ('hrm' in col_name_lower or 'hr' in col_name_lower or 'humitat' in col_name_lower or 'humidity' in col_name_lower) and ('%' in col_name):
                columna_mapping['hr'] = idx
            # Precipitació
            elif ('ppt' in col_name_lower or 'precipitació' in col_name_lower or 'precipitacio' in col_name_lower or 
                  'pluja' in col_name_lower or 'precipitation' in col_name_lower) and ('mm' in col_name):
                columna_mapping['ppt'] = idx
            # Gruix de neu (GN)
            elif ('gn' in col_name_lower or 'neu' in col_name_lower or 'snow' in col_name_lower or 'gruix' in col_name_lower) and ('cm' in col_name):
                columna_mapping['gn'] = idx
            # Vent mitjà (VVM)
            elif ('vvm' in col_name_lower or ('vent' in col_name_lower and 'mitj' in col_name_lower) or 
                  'wind' in col_name_lower) and ('km/h' in col_name or 'km' in col_name_lower):
                columna_mapping['vvm'] = idx
            # Direcció vent (DVM)
            elif ('dvm' in col_name_lower or 'direcció' in col_name_lower or 'direccio' in col_name_lower or 
                  'direction' in col_name_lower) and ('graus' in col_name_lower or '°' in col_name or 'degrees' in col_name_lower):
                columna_mapping['dvm'] = idx
            # Vent màxim (VVX)
            elif ('vvx' in col_name_lower or ('vent' in col_name_lower and 'màx' in col_name_lower) or 
                  'max' in col_name_lower) and ('km/h' in col_name or 'km' in col_name_lower):
                columna_mapping['vvx'] = idx
            # Pressió (PM)
            elif ('pm' in col_name_lower or 'pressió' in col_name_lower or 'pressio' in col_name_lower or 
                  'pressure' in col_name_lower) and ('hpa' in col_name_lower or 'hpa' in col_name):
                columna_mapping['pm'] = idx
            # Radiació solar (RS)
            elif ('rs' in col_name_lower or 'radiació' in col_name_lower or 'radiacio' in col_name_lower or 
                  'radiation' in col_name_lower) and ('w/m²' in col_name_lower or 'w/m2' in col_name_lower):
                columna_mapping['rs'] = idx
        
        # Si no hem trobat algunes columnes bàsiques, fem un mapeig per posició
        if 'tm' not in columna_mapping and len(columnes) > 1:
            # Suposem que TM és la segona columna (índex 1) si conté °C
            if len(columnes) > 1 and '°c' in columnes[1]:
                columna_mapping['tm'] = 1
        
        write_log(f"🔍 Mapeig de columnes: {columna_mapping}")
        
        # Busquem des del FINAL (dades més recents)
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all(['td', 'th'])
            
            if len(cells) < 2:  # Almenys període i una dada
                continue
                
            periode = cells[0].get_text(strip=True)
            
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                # Inicialitzem dades
                dades_extretes = {
                    'station_name': station_name,
                    'station_code': url.split('codi=')[1][:2] if 'codi=' in url else '',
                    'periode': periode
                }
                
                # Processem cada columna mapejada
                for key, col_idx in columna_mapping.items():
                    if col_idx < len(cells):
                        valor = cells[col_idx].get_text(strip=True)
                        # No processem 'periode' ja que ja el tenim
                        if key != 'periode':
                            dades_extretes[key] = convertir_a_numero(valor)
                
                # Netegem les dades que no existeixen (valor None)
                dades_finales = {k: v for k, v in dades_extretes.items() if v is not None}
                
                write_log(f"✅ Dades RECENTS trobades: {periode}")
                write_log("📊 Dades extretes:")
                for key, value in dades_finales.items():
                    if key not in ['station_name', 'station_code', 'periode']:
                        write_log(f"   • {key}: {value}")
                
                # Verifiquem que tenim dades suficients
                if len([k for k in dades_finales.keys() if k not in ['station_name', 'station_code', 'periode']]) > 0:
                    return dades_finales
                else:
                    write_log("⚠️  Dades insuficients, buscant més...")
        
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
    """Converteix hora TU (UTC) a hora local (CET/CEST) - VERSIÓ AMB HORARI D'ESTIU"""
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
        
        # Obtenir la data actual en UTC per saber si és CET o CEST
        utc_now = datetime.now(pytz.utc)
        local_tz = pytz.timezone('Europe/Madrid')
        local_now = utc_now.astimezone(local_tz)
        
        # Calcular offset de l'hora local respecte UTC (en hores)
        offset_hours = int(local_now.utcoffset().total_seconds() / 3600)
        
        def convertir_hora(hora):
            hora = hora.strip()
            if ':' in hora:
                try:
                    h_str, m_part = hora.split(':', 1)
                    # Agafar només els dos primers dígits dels minuts
                    m_str = m_part[:2] if len(m_part) >= 2 else '00'
                    
                    h = int(h_str)
                    m = int(m_str) if m_str.isdigit() else 0
                    
                    # Sumar l'offset actual (1 per CET, 2 per CEST)
                    h_local = h + offset_hours
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
            'name': 'Girona',
            'code': 'XJ',
            'url': 'https://www.meteo.cat/observacions/xema/dades?codi=XJ'
        },
        {
            'name': 'Fornells de la Selva',
            'code': 'UO',
            'url': 'https://www.meteo.cat/observacions/xema/dades?codi=UO'
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
            f"Actualitzat: {display_time.strftime('%H:%M')}"
        ]
        
        # Afegir període si existeix
        if 'periode' in dades and dades['periode']:
            parts_cat.append(f"Període: {dades['periode']}")
        
        # Només afegim els camps que existeixen
        if 'tm' in dades and dades['tm'] is not None:
            parts_cat.append(f"🌡️ Temp. Mitjana: {dades['tm']}°C")
        
        if 'tx' in dades and dades['tx'] is not None:
            parts_cat.append(f"🔥 Temp. Màxima: {dades['tx']}°C")
            
        if 'tn' in dades and dades['tn'] is not None:
            parts_cat.append(f"❄️ Temp. Mínima: {dades['tn']}°C")
        
        if 'hr' in dades and dades['hr'] is not None:
            parts_cat.append(f"💧 Humitat: {dades['hr']}%")
        
        if 'ppt' in dades and dades['ppt'] is not None:
            parts_cat.append(f"🌧️ Precipitació: {dades['ppt']}mm")
        
        # Afegir gruix de neu SOLAMENT si existeix
        if 'gn' in dades and dades['gn'] is not None and dades['gn'] != 0:
            parts_cat.append(f"❄️ Gruix de neu: {dades['gn']}cm")
        
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
            f"Updated: {display_time.strftime('%H:%M')}"
        ]
        
        # Afegir període si existeix
        if 'periode' in dades and dades['periode']:
            parts_en.append(f"Period: {dades['periode']}")
        
        # Només afegim els camps que existeixen
        if 'tm' in dades and dades['tm'] is not None:
            parts_en.append(f"🌡️ Avg Temp: {dades['tm']}°C")
        
        if 'tx' in dades and dades['tx'] is not None:
            parts_en.append(f"🔥 Max Temp: {dades['tx']}°C")
            
        if 'tn' in dades and dades['tn'] is not None:
            parts_en.append(f"❄️ Min Temp: {dades['tn']}°C")
        
        if 'hr' in dades and dades['hr'] is not None:
            parts_en.append(f"💧 Humidity: {dades['hr']}%")
        
        if 'ppt' in dades and dades['ppt'] is not None:
            parts_en.append(f"🌧️ Precipitation: {dades['ppt']}mm")
        
        # Afegir gruix de neu SOLAMENT si existeix
        if 'gn' in dades and dades['gn'] is not None and dades['gn'] != 0:
            parts_en.append(f"❄️ Snow depth: {dades['gn']}cm")
        
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
