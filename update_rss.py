import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys
import os
import time

def write_log(message):
    """Escriu un missatge al log i també el mostra per pantalla"""
    print(message)
    with open('debug.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def get_current_station():
    """Alterna entre estacions basant-se en la HORA actual"""
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    
    # Utilitzem la combinació hora+minut per alternar
    # Si (hora + minut) és parell: Girona, si és senar: Fornells
    total = current_hour + current_minute
    if total % 2 == 0:
        return {"code": "XJ", "name": "Girona"}
    else:
        return {"code": "UO", "name": "Fornells de la Selva"}

def get_meteo_data(station_code, station_name):
    try:
        write_log("="*60)
        write_log(f"🚀 INICIANT get_meteo_data() - Estació {station_name} [{station_code}]")
        write_log(f"⏰ Hora: {datetime.now()}")
        
        write_log(f"🌐 Connectant a Meteo.cat - Estació {station_name} [{station_code}]...")
        url = f"https://www.meteo.cat/observacions/xema/dades?codi={station_code}"
        write_log(f"🔗 URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        write_log("✅ Connexió exitosa")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        write_log("✅ HTML parsejat correctament")
        
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            write_log("❌ No s'ha trobat la taula 'tblperiode'")
            return None
            
        write_log("✅ Taula 'tblperiode' trobada")
            
        rows = table.find_all('tr')
        write_log(f"📊 Files a la taula: {len(rows)}")
        
        if not rows:
            write_log("❌ La taula no té files")
            return None
        
        write_log("\n🔍 CERCANT PERÍODE MÉS RECENT AMB DADES VÀLIDES...")
        
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all(['td', 'th'])
            
            if len(cells) < 6:
                continue
                
            periode = cells[0].get_text(strip=True)
            
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                write_log(f"   ✅ PERÍODE VÀLID TROBAT: '{periode}'")
                
                dades_valides = False
                for idx in range(1, min(6, len(cells))):
                    text = cells[idx].get_text(strip=True)
                    if text and text != '(s/d)' and text != '-':
                        dades_valides = True
                        break
                
                if dades_valides:
                    write_log(f"   🎯 TE DADES VÀLIDES - PROCESSANT...")
                    
                    # Extracció de dades
                    tm = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    tx = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    tn = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    hr = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                    ppt = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                    
                    write_log("   📊 DADES EXTRAÏDES:")
                    write_log(f"      TM: '{tm}' | TX: '{tx}' | TN: '{tn}'")
                    write_log(f"      HR: '{hr}' | PPT: '{ppt}'")
                    
                    def a_numero(text, default=0.0):
                        if not text or text == '(s/d)' or text == '-':
                            return default
                        try:
                            return float(text.replace(',', '.'))
                        except:
                            return default
                    
                    tm_num = a_numero(tm)
                    tx_num = a_numero(tx, tm_num)
                    tn_num = a_numero(tn, tm_num)
                    hr_num = a_numero(hr)
                    ppt_num = a_numero(ppt)
                    
                    periode_ajustat = ajustar_periode(periode)
                    
                    write_log(f"   ✅ DADES OBTINGUDES CORRECTAMENT")
                    write_log(f"   🕒 Període ajustat: {periode} → {periode_ajustat}")
                    
                    return {
                        'station_name': station_name,
                        'station_code': station_code,
                        'periode': periode_ajustat,
                        'tm': tm_num, 'tx': tx_num, 'tn': tn_num,
                        'hr': hr_num, 'ppt': ppt_num
                    }
        
        write_log("❌ CAP FILA TE DADES VÀLIDES")
        return None
        
    except Exception as e:
        write_log(f"❌ ERROR CRÍTIC a get_meteo_data(): {str(e)}")
        import traceback
        write_log(f"TRACEBACK: {traceback.format_exc()}")
        return None

def ajustar_periode(periode_str):
    try:
        write_log(f"   🕒 Ajustant període: {periode_str}")
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
            
            adjusted = f"{start_adj:02d}:{minut_inici:02d}-{end_adj:02d}:{minut_fi:02d}"
            write_log(f"   🕒 PERÍODE AJUSTAT: {periode_str} TU → {adjusted}")
            return adjusted
            
    except Exception as e:
        write_log(f"   ❌ Error ajustant període: {e}")
    
    return periode_str

def generar_rss():
    write_log("\n" + "="*60)
    write_log("🚀 INICIANT GENERACIÓ RSS")
    
    # Triem quina estació consultar
    station = get_current_station()
    write_log(f"🎯 ESTACIÓ SELECCIONADA: {station['name']} [{station['code']}]")
    
    dades = get_meteo_data(station['code'], station['name'])
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES")
        write_log("💤 NO S'ACTUALITZA RSS")
        return False
    
    write_log("✅ DADES OBTINGUDES - GENERANT RSS")
    
    # Títol en català i anglès
    titol_cat = (
        f"🌤️ {dades['station_name']} | Actualitzat: {current_time} | Període: {dades['periode']} | "
        f"Temp. Mitjana: {dades['tm']}°C | Temp. Màxima: {dades['tx']}°C | Temp. Mínima: {dades['tn']}°C | "
        f"Humitat: {dades['hr']}% | Precipitació: {dades['ppt']}mm"
    )
    
    titol_en = (
        f"🌤️ {dades['station_name']} | Updated: {current_time} | Period: {dades['periode']} | "
        f"Avg Temp: {dades['tm']}°C | Max Temp: {dades['tx']}°C | Min Temp: {dades['tn']}°C | "
        f"Humidity: {dades['hr']}% | Precipitation: {dades['ppt']}mm"
    )
    
    titol = f"{titol_cat} || {titol_en}"
    
    write_log(f"📝 Títol generat ({len(titol)} caràcters)")
    
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
    <description>Dades meteorològiques automàtiques de l'estació de {dades['station_name']} ({dades['station_code']})</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    write_log("📁 Intentant escriure el fitxer meteo.rss...")
    
    try:
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        write_log("✅ RSS guardat a 'meteo.rss'")
        return True
        
    except Exception as e:
        write_log(f"❌ ERROR escrivint el fitxer: {str(e)}")
        return False

if __name__ == "__main__":
    # Netejar log anterior
    if os.path.exists('debug.log'):
        os.remove('debug.log')
    
    with open('debug.log', 'w', encoding='utf-8') as f:
        f.write("=== DEBUG LOG METEO.CAT - ESTACIONS ALTERNANTS ===\n")
        f.write(f"Inici: {datetime.now()}\n")
    
    write_log("🚀 SCRIPT INICIAT - ESTACIONS ALTERNANTS (GIRONA I FORNELLS)")
    
    exit = generar_rss()
    
    if exit:
        write_log("🎉 ÈXIT - RSS ACTUALITZAT CORRECTAMENT")
    else:
        write_log("💤 NO S'HA ACTUALITZAT RSS")
    
    write_log("="*60)
    write_log(f"🏁 FI DE L'EXECUCIÓ - {datetime.now()}")
    
    sys.exit(0 if exit else 1)
