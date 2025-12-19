#!/usr/bin/env python3
# daily_weather_scraper.py - VERSIÓ COMPLETA DEL DIA
# PAS 1: Scrapeja TOTES les dades del dia i calcula màximes/mínimes/acumulats

import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import json
import csv
import os

def write_log(message):
    """Escriu un missatge al log i també el mostra per pantalla"""
    print(message)
    with open('debug_daily.log', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def get_today_date_spanish():
    """Retorna la data actual en format dd/mm/aaaa"""
    return datetime.now().strftime('%d/%m/%Y')

def convertir_a_numero(text, default=None):
    """Converteix text a número, retorna None si no és vàlid"""
    if not text or text in ['(s/d)', '-', '', 'n/d', 'N/D']:
        return None
    try:
        # Netejar possibles símboles
        text = text.replace(',', '.').replace('°', '').replace('mm', '').replace('hPa', '').replace('W/m²', '')
        return float(text.strip())
    except:
        return None

def convertir_hora_tu_a_local(hora_tu_str):
    """Converteix hora TU (UTC) a hora local (CET = UTC+1)"""
    if not hora_tu_str:
        return hora_tu_str
    
    try:
        # Netejar i normalitzar
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

def scrape_all_today_data(url, station_name):
    """
    Extreu TOTES les dades del dia actual de l'estació
    
    Retorna:
    - periods_data: Llista amb totes les dades de cada període
    - summary_data: Diccionari amb resums (màximes, mínimes, acumulats)
    """
    try:
        write_log(f"\n🌐 Connectant a {station_name}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'tblperiode'})
        
        if not table:
            write_log("❌ No s'ha trobat la taula tblperiode")
            return None, None
        
        # Trobar totes les files de dades
        rows = table.find_all('tr')
        write_log(f"📊 Total files trobades a la taula: {len(rows)}")
        
        # Llista per emmagatzemar totes les dades del dia
        all_periods = []
        
        # Variables per a càlculs acumulats
        temp_max_values = []
        temp_min_values = []
        rain_values = []
        
        # Data actual per filtrar (si calgués)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Recórrer totes les files (excepte capçaleres)
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            
            # Necessitem almenys 6 columnes per tenir dades completes
            if len(cells) < 6:
                continue
            
            periode = cells[0].get_text(strip=True)
            
            # Verificar si és un període vàlid (hh:mm - hh:mm)
            if re.match(r'\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}', periode):
                # Convertir hora TU a local
                periode_local = convertir_hora_tu_a_local(periode)
                
                # Extreure totes les dades disponibles
                period_data = {
                    'station_name': station_name,
                    'date': today,
                    'period': periode_local,
                    'tm': convertir_a_numero(cells[1].get_text(strip=True)) if len(cells) > 1 else None,  # Temp mitjana
                    'tx': convertir_a_numero(cells[2].get_text(strip=True)) if len(cells) > 2 else None,  # Temp màxima
                    'tn': convertir_a_numero(cells[3].get_text(strip=True)) if len(cells) > 3 else None,  # Temp mínima
                    'hr': convertir_a_numero(cells[4].get_text(strip=True)) if len(cells) > 4 else None,  # Humitat
                    'ppt': convertir_a_numero(cells[5].get_text(strip=True)) if len(cells) > 5 else None, # Pluja
                }
                
                # Afegir dades addicionals si existeixen
                if len(cells) > 6:
                    period_data['vvm'] = convertir_a_numero(cells[6].get_text(strip=True))  # Vent mitjà
                if len(cells) > 7:
                    period_data['dvm'] = convertir_a_numero(cells[7].get_text(strip=True))  # Direcció vent
                if len(cells) > 8:
                    period_data['vvx'] = convertir_a_numero(cells[8].get_text(strip=True))  # Vent màxim
                if len(cells) > 9:
                    period_data['pm'] = convertir_a_numero(cells[9].get_text(strip=True))   # Pressió
                if len(cells) > 10:
                    period_data['rs'] = convertir_a_numero(cells[10].get_text(strip=True))  # Radiació
                
                # Només afegir si tenim almenys alguna dada de temperatura o pluja
                if period_data['tx'] is not None or period_data['tn'] is not None or period_data['ppt'] is not None:
                    all_periods.append(period_data)
                    
                    # Acumular per a càlculs
                    if period_data['tx'] is not None:
                        temp_max_values.append(period_data['tx'])
                    if period_data['tn'] is not None:
                        temp_min_values.append(period_data['tn'])
                    if period_data['ppt'] is not None:
                        rain_values.append(period_data['ppt'])
                    
                    write_log(f"   ✅ Període: {periode_local} | TX: {period_data['tx']} | TN: {period_data['tn']} | Pluja: {period_data['ppt']}")
        
        write_log(f"📈 Total períodes vàlids trobats: {len(all_periods)}")
        
        if not all_periods:
            write_log("❌ No s'han trobat dades vàlides per al dia d'avui")
            return None, None
        
        # Calcular resums
        summary = {
            'station_name': station_name,
            'date': today,
            'date_spanish': get_today_date_spanish(),
            'last_period': all_periods[-1]['period'] if all_periods else "N/D",
            'updated_at': datetime.now().strftime('%H:%M'),
            'total_periods': len(all_periods),
            'max_temp': max(temp_max_values) if temp_max_values else None,
            'min_temp': min(temp_min_values) if temp_min_values else None,
            'total_rain': sum(rain_values) if rain_values else 0.0,
            'periods_with_data': {
                'temp_max': len(temp_max_values),
                'temp_min': len(temp_min_values),
                'rain': len(rain_values)
            }
        }
        
        write_log(f"📊 RESUM CALCULAT:")
        write_log(f"   • Màxima del dia: {summary['max_temp']}°C")
        write_log(f"   • Mínima del dia: {summary['min_temp']}°C")
        write_log(f"   • Pluja acumulada: {summary['total_rain']}mm")
        write_log(f"   • Últim període: {summary['last_period']}")
        
        return all_periods, summary
        
    except Exception as e:
        write_log(f"❌ Error consultant dades completes: {e}")
        return None, None

def save_to_json(data, filename):
    """Guarda les dades en format JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        write_log(f"💾 Dades guardades a {filename}")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant JSON: {e}")
        return False

def save_to_csv(periods_data, filename):
    """Guarda les dades en format CSV"""
    try:
        if not periods_data:
            write_log("⚠️  No hi ha dades per guardar en CSV")
            return False
        
        # Crear capçaleres basades en les claus del primer element
        fieldnames = list(periods_data[0].keys())
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(periods_data)
        
        write_log(f"💾 Dades guardades a {filename} ({len(periods_data)} registres)")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant CSV: {e}")
        return False

def main():
    """Funció principal"""
    
    write_log("=" * 60)
    write_log("🌤️  DAILY WEATHER SCRAPER - VERSIÓ COMPLETA DEL DIA")
    write_log("=" * 60)
    
    # Configuració de les estacions
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
        }
    ]
    
    # Crear directori data si no existeix
    os.makedirs('data', exist_ok=True)
    
    # Diccionari per emmagatzemar totes les dades
    all_data = {
        'metadata': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stations': len(stations)
        },
        'stations': {}
    }
    
    # Processar cada estació
    for station in stations:
        write_log(f"\n{'='*50}")
        write_log(f"📡 Processant: {station['name']} [{station['code']}]")
        
        # Obtenir totes les dades del dia
        periods_data, summary_data = scrape_all_today_data(station['url'], station['name'])
        
        if periods_data and summary_data:
            # Guardar a l'estructura principal
            all_data['stations'][station['code']] = {
                'info': {
                    'name': station['name'],
                    'code': station['code'],
                    'url': station['url']
                },
                'periods': periods_data,
                'summary': summary_data
            }
            
            # Guardar CSV individual per estació (opcional)
            csv_filename = f"data/{station['code']}_{datetime.now().strftime('%Y%m%d')}.csv"
            save_to_csv(periods_data, csv_filename)
            
            write_log(f"✅ {station['name']}: {len(periods_data)} períodes processats")
        else:
            write_log(f"❌ {station['name']}: No s'han pogut obtenir dades")
            # Crear estructura buida
            all_data['stations'][station['code']] = {
                'info': {
                    'name': station['name'],
                    'code': station['code'],
                    'url': station['url']
                },
                'periods': [],
                'summary': None
            }
    
    # Guardar totes les dades en un sol fitxer JSON
    json_filename = f"data/weather_daily_{datetime.now().strftime('%Y%m%d')}.json"
    save_to_json(all_data, json_filename)
    
    # Guardar també un fitxer de resum per al HTML
    summary_for_html = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date_spanish': get_today_date_spanish(),
        'stations': {}
    }
    
    for station_code, data in all_data['stations'].items():
        if data['summary']:
            summary_for_html['stations'][station_code] = data['summary']
    
    save_to_json(summary_for_html, 'data/weather_summary.json')
    
    # Mostrar resum final
    write_log("\n" + "=" * 60)
    write_log("📋 RESUM FINAL DEL DIA")
    write_log("=" * 60)
    
    for station_code, data in all_data['stations'].items():
        if data['summary']:
            summary = data['summary']
            write_log(f"\n📍 {summary['station_name']}:")
            write_log(f"   • Períodes: {summary['total_periods']}")
            write_log(f"   • Màxima: {summary['max_temp']}°C")
            write_log(f"   • Mínima: {summary['min_temp']}°C")
            write_log(f"   • Pluja: {summary['total_rain']}mm")
            write_log(f"   • Últim període: {summary['last_period']}")
        else:
            write_log(f"\n⚠️  {station_code}: Sense dades")
    
    write_log(f"\n💾 Fitxers generats:")
    write_log(f"   • data/weather_summary.json (per HTML)")
    write_log(f"   • data/weather_daily_YYYYMMDD.json (complet)")
    write_log(f"   • data/XX_YYYYMMDD.csv (per estació)")
    
    write_log("\n✅ PROCÉS COMPLETAT")
    write_log("=" * 60)
    
    return all_data

if __name__ == "__main__":
    # Netejar log anterior
    with open('debug_daily.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI DAILY SCRAPER: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    try:
        result = main()
        if result['metadata']['total_stations'] > 0:
            print("\n🎉 Daily scraper executat amb èxit!")
            print("📊 Revisa debug_daily.log per més detalls")
        else:
            print("\n⚠️  No s'han processat estacions")
    except Exception as e:
        write_log(f"💥 ERROR CRÍTIC: {e}")
        print(f"\n❌ Error durant l'execució: {e}")