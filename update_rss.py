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

def get_meteo_data_fornells():
    try:
        write_log("="*60)
        write_log("🚀 INICIANT get_meteo_data_fornells() - Estació FORNELLS [UO]")
        write_log(f"⏰ Hora: {datetime.now()}")
        
        write_log("🌐 Connectant a Meteo.cat - Estació Fornells de la Selva [UO]...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=UO"
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
            
            if len(cells) < 11:
                continue
                
            periode = cells[0].get_text(strip=True)
            
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                write_log(f"   ✅ PERÍODE VÀLID TROBAT: '{periode}'")
                
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
        
        write_log("❌ CAP FILA TE DADES VÀLIDES")
        return None
        
    except Exception as e:
        write_log(f"❌ ERROR CRÍTIC a get_meteo_data_fornells(): {str(e)}")
        import traceback
        write_log(f"TRACEBACK: {traceback.format_exc()}")
        return None

def ajustar_periode(periode_str):
    try:
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
            return adjusted
            
    except Exception as e:
        write_log(f"   ❌ Error ajustant període: {e}")
    
    return periode_str

def generar_rss_fornells():
    write_log("\n" + "="*60)
    write_log("🚀 INICIANT GENERACIÓ RSS - FORNELLS")
    
    dades = get_meteo_data_fornells()
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES DE FORNELLS")
        return False
    
    write_log("✅ DADES OBTINGUDES - GENERANT RSS FOR FORNELLS")
    
    titol_cat = (
        f"🌤️ FORNELLS DE LA SELVA | Actualitzat: {current_time} | Període: {dades['periode']} | "
        f"Temp. Mitjana: {dades['tm']}°C | Temp. Màxima: {dades['tx']}°C | Temp. Mínima: {dades['tn']}°C | "
        f"Humitat: {dades['hr']}% | Precipitació: {dades['ppt']}mm"
    )
    
    titol_en = (
        f"🌤️ FORNELLS DE LA SELVA | Updated: {current_time} | Period: {dades['periode']} | "
        f"Avg Temp: {dades['tm']}°C | Max Temp: {dades['tx']}°C | Min Temp: {dades['tn']}°C | "
        f"Humidity: {dades['hr']}% | Precipitation: {dades['ppt']}mm"
    )
    
    titol = f"{titol_cat} || {titol_en}"
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Fornells de la Selva</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estació Fornells de la Selva [UO]</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat/observacions/xema/dades?codi=UO</link>
    <description>Dades meteorològiques automàtiques de l'estació de Fornells de la Selva (UO)</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    try:
        with open('meteo_fornells.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        write_log("✅ RSS FORNELLS guardat a 'meteo_fornells.rss'")
        return True
        
    except Exception as e:
        write_log(f"❌ ERROR escrivint el fitxer: {str(e)}")
        return False

if __name__ == "__main__":
    # Netejar log anterior
    if os.path.exists('debug_fornells.log'):
        os.remove('debug_fornells.log')
    
    with open('debug_fornells.log', 'w', encoding='utf-8') as f:
        f.write("=== DEBUG LOG FORNELLS DE LA SELVA [UO] ===\n")
        f.write(f"Inici: {datetime.now()}\n")
    
    write_log("🚀 SCRIPT FORNELLS INICIAT - ESTACIÓ UO")
    
    exit = generar_rss_fornells()
    
    if exit:
        write_log("🎉 ÈXIT - RSS FORNELLS ACTUALITZAT CORRECTAMENT")
    else:
        write_log("💤 NO S'HA ACTUALITZAT RSS FORNELLS")
    
    write_log("="*60)
    write_log(f"🏁 FI DE L'EXECUCIÓ FORNELLS - {datetime.now()}")
    
    sys.exit(0 if exit else 1)
