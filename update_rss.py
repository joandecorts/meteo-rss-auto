import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys
import os
import time  # Nou import per als reintents

def write_log(message):
    """Escriu un missatge al log i també el mostra per pantalla"""
    print(message)
    with open('debug.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def get_meteo_data():
    try:
        write_log("="*60)
        write_log("🚀 INICIANT get_meteo_data()")
        write_log(f"⏰ Hora: {datetime.now()}")
        
        write_log("🌐 Connectant a Meteo.cat - Estació Girona [XJ]...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=XJ"
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
        
        write_log("\n🔍 ANALITZANT ESTRUCTURA REAL DE LES FILES...")
        
        for i in range(min(3, len(rows))):
            write_log(f"\n--- FILA {i} (estructura) ---")
            all_cells = rows[i].find_all(['td', 'th'])
            write_log(f"   Total elements (td+th): {len(all_cells)}")
            
            for j, cell in enumerate(all_cells):
                write_log(f"   Element {j} ({cell.name}): '{cell.get_text(strip=True)}'")
        
        write_log("\n🔍 CERCANT PERÍODE MÉS RECENT AMB DADES VÀLIDES...")
        write_log("ℹ️  NOTA: Les files de dades reals tenen 11 columnes (th + 10 td)")
        
        for i in range(len(rows)-1, 0, -1):
            write_log(f"\n--- ANALITZANT FILA {i} ---")
            cells = rows[i].find_all(['td', 'th'])
            write_log(f"   Cel·les (td+th): {len(cells)}")
            
            if len(cells) < 11:
                write_log(f"   ❌ Només té {len(cells)} columnes - necessitem 11")
                continue
                
            periode = cells[0].get_text(strip=True)
            write_log(f"   Període: '{periode}'")
            
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                write_log(f"   ✅ FORMAT DE PERÍODE VÀLID")
                
                write_log("   📊 CONTINGUT DE LES 11 COLUMNES:")
                for idx in range(min(11, len(cells))):
                    text = cells[idx].get_text(strip=True)
                    cell_type = cells[idx].name
                    write_log(f"      Columna {idx} ({cell_type}): '{text}'")
                
                dades_valides = False
                for idx in range(1, min(11, len(cells))):
                    text = cells[idx].get_text(strip=True)
                    if text and text != '(s/d)':
                        dades_valides = True
                        break
                
                if dades_valides:
                    write_log(f"   🎯 TE DADES VÀLIDES - PROCESSANT...")
                    
                    tm = cells[1].get_text(strip=True)
                    tx = cells[2].get_text(strip=True)
                    tn = cells[3].get_text(strip=True)
                    hr = cells[4].get_text(strip=True)
                    ppt = cells[5].get_text(strip=True)
                    vvm = cells[6].get_text(strip=True)
                    dvm = cells[7].get_text(strip=True)
                    vvx = cells[8].get_text(strip=True)
                    pm = cells[9].get_text(strip=True)
                    rs = cells[10].get_text(strip=True)
                    
                    write_log("   📊 DADES EXTRAÏDES:")
                    write_log(f"      TM: '{tm}' | TX: '{tx}' | TN: '{tn}'")
                    write_log(f"      HR: '{hr}' | PPT: '{ppt}' | VVM: '{vvm}'")
                    write_log(f"      DVM: '{dvm}' | VVX: '{vvx}' | PM: '{pm}'")
                    write_log(f"      RS: '{rs}'")
                    
                    def a_numero(text, default=0.0):
                        if not text or text == '(s/d)':
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
                    vvm_num = a_numero(vvm)
                    dvm_num = a_numero(dvm)
                    vvx_num = a_numero(vvx)
                    pm_num = a_numero(pm)
                    rs_num = a_numero(rs)
                    
                    periode_ajustat = ajustar_periode(periode)
                    
                    write_log(f"   ✅ DADES OBTINGUDES CORRECTAMENT")
                    write_log(f"   🕒 Període ajustat: {periode} → {periode_ajustat}")
                    
                    return {
                        'periode': periode_ajustat,
                        'tm': tm_num, 'tx': tx_num, 'tn': tn_num,
                        'hr': hr_num, 'ppt': ppt_num, 'vvm': vvm_num,
                        'dvm': dvm_num, 'vvx': vvx_num, 'pm': pm_num,
                        'rs': rs_num
                    }
                else:
                    write_log(f"   ❌ NO TE DADES VÀLIDES - Cercant fila anterior...")
            else:
                write_log(f"   ❌ FORMAT DE PERÍODE INVÀLID - Cercant fila anterior...")
        
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
        match = re.match(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', periode_str)
        if match:
            hora_inici = int(match.group(1).split(':')[0])
            minut_inici = int(match.group(1).split(':')[1])
            hora_fi = int(match.group(2).split(':')[0])
            minut_fi = int(match.group(2).split(':')[1])
            
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
    
    dades = get_meteo_data()
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES")
        write_log("💤 NO S'ACTUALITZA RSS")
        return False
    
    write_log("✅ DADES OBTINGUDES - GENERANT RSS")
    
    titol_cat = (
        f"🌤️ GIRONA | Actualitzat: {current_time} | Període: {dades['periode']} | "
        f"Temp. Mitjana: {dades['tm']}°C | Temp. Màxima: {dades['tx']}°C | Temp. Mínima: {dades['tn']}°C | "
        f"Humitat: {dades['hr']}% | Precipitació: {dades['ppt']}mm | "
        f"Vent Mitjà: {dades['vvm']}km/h | Direcció Vent: {dades['dvm']}° | "
        f"Vent Màxim: {dades['vvx']}km/h | Pressió: {dades['pm']}hPa | "
        f"Radiació Solar: {dades['rs']}W/m²"
    )
    
    titol_en = (
        f"🌤️ GIRONA | Updated: {current_time} | Period: {dades['periode']} | "
        f"Avg Temp: {dades['tm']}°C | Max Temp: {dades['tx']}°C | Min Temp: {dades['tn']}°C | "
        f"Humidity: {dades['hr']}% | Precipitation: {dades['ppt']}mm | "
        f"Avg Wind: {dades['vvm']}km/h | Wind Direction: {dades['dvm']}° | "
        f"Max Wind: {dades['vvx']}km/h | Pressure: {dades['pm']}hPa | "
        f"Solar Radiation: {dades['rs']}W/m²"
    )
    
    titol = f"{titol_cat} || {titol_en}"
    
    write_log(f"📝 Títol generat ({len(titol)} caràcters)")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Girona</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estació Girona [XJ] - Real-time weather data</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat/observacions/xema/dades?codi=XJ</link>
    <description>Dades meteorològiques automàtiques de l'estació de Girona (XJ) - Automatic weather data from Girona station (XJ)</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    write_log("📁 Intentant escriure el fitxer meteo.rss...")
    
    try:
        ruta_completa = os.path.abspath('meteo.rss')
        write_log(f"📍 Ruta completa del fitxer: {ruta_completa}")
        
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        write_log("✅ RSS guardat a 'meteo.rss'")
        
        if os.path.exists('meteo.rss'):
            mida = os.path.getsize('meteo.rss')
            write_log(f"📏 Mida del fitxer: {mida} bytes")
            
            with open('meteo.rss', 'r', encoding='utf-8') as f:
                primeres_linies = f.readlines()[:3]
                write_log("📄 Primeres línies del fitxer:")
                for i, linia in enumerate(primeres_linies):
                    write_log(f"   Línia {i}: {linia.strip()}")
        else:
            write_log("❌ El fitxer meteo.rss NO existeix després d'escriure!")
            
        return True
        
    except Exception as e:
        write_log(f"❌ ERROR escrivint el fitxer: {str(e)}")
        import traceback
        write_log(f"TRACEBACK: {traceback.format_exc()}")
        return False

def main_amb_reintents():
    """Funció principal amb sistema de reintents intel·ligent"""
    max_intents = 3
    espera_entre_intents = 300  # 5 minuts en segons
    
    write_log("🔄 SISTEMA DE REINTENTS ACTIVAT")
    write_log(f"🎯 Configuració: {max_intents} intents màxims, {espera_entre_intents}s entre intents")

    for intent in range(max_intents):
        write_log(f"\n{'='*50}")
        write_log(f"🔄 INTENT {intent + 1}/{max_intents}")
        write_log(f"⏰ Hora inici intent: {datetime.now()}")
        
        exit = generar_rss()
        
        if exit:
            write_log("✅ ÈXIT - RSS actualitzat correctament")
            return True
        else:
            if intent < max_intents - 1:
                write_log(f"⏰ Esperant {espera_entre_intents} segons per proper intent...")
                # Mostrem compte enrere cada 30 segons
                for i in range(espera_entre_intents // 30):
                    time.sleep(30)
                    write_log(f"   ⏳ Temps restant: {espera_entre_intents - (i+1)*30} segons")
            else:
                write_log("❌ TOTS ELS INTENTS HAN FALLAT")
    
    return False

if __name__ == "__main__":
    # Netejar log anterior
    if os.path.exists('debug.log'):
        os.remove('debug.log')
    
    directori_actual = os.getcwd()
    
    with open('debug.log', 'w', encoding='utf-8') as f:
        f.write("=== DEBUG LOG METEO.CAT - ESTACIÓ XJ (GIRONA) ===\n")
        f.write(f"Inici: {datetime.now()}\n")
        f.write(f"Directori actual: {directori_actual}\n")
        f.write("="*60 + "\n")
    
    write_log("🚀 SCRIPT INICIAT - ESTACIÓ XJ (GIRONA)")
    write_log(f"🐍 Versió Python: {sys.version}")
    write_log(f"📁 Directori de treball: {directori_actual}")
    write_log(f"⏰ Hora d'inici: {datetime.now()}")
    
    # Cridem la nova funció amb reintents
    exit = main_amb_reintents()
    
    if exit:
        write_log("🎉 ÈXIT - RSS ACTUALITZAT CORRECTAMENT")
    else:
        write_log("💤 NO S'HA ACTUALITZAT RSS - Tots els intents han fallat")
    
    write_log("="*60)
    write_log(f"🏁 FI DE L'EXECUCIÓ - {datetime.now()}")
    
    # Sortim amb 0 si èxit, 1 si fallada
    sys.exit(0 if exit else 1)
