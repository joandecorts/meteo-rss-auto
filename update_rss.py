import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys
import os

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
        
        # ✅ ESTACIÓ CORRECTA: XJ (Girona)
        write_log("🌐 Connectant a Meteo.cat - Estació Girona [XJ]...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=XJ"
        write_log(f"🔗 URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        write_log("✅ Connexió exitosa")
        write_log(f"📄 Codi resposta: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        write_log("✅ HTML parsejat correctament")
        
        # Buscar la taula 'tblperiode'
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
        
        # Mostrar les CAPÇALERES
        header_cells = rows[0].find_all(['th', 'td'])
        header_texts = [cell.get_text(strip=True) for cell in header_cells]
        write_log(f"📋 CAPÇALERES: {header_texts}")
        write_log(f"📋 Número de columnes: {len(header_texts)}")
        
        # Recórrer des de l'última fila (més recent) fins a la primera
        write_log("\n🔍 CERCANT PERÍODE MÉS RECENT AMB DADES VÀLIDES...")
        
        for i in range(len(rows)-1, 0, -1):
            write_log(f"\n--- FILA {i} ---")
            cells = rows[i].find_all('td')
            write_log(f"   Cel·les: {len(cells)}")
            
            if not cells or len(cells) < 11:
                write_log("   ❌ No té suficients columnes")
                continue
                
            periode = cells[0].get_text(strip=True)
            write_log(f"   Període: '{periode}'")
            
            # Verificar si és un període vàlid (format hh:mm-hh:mm)
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                write_log(f"   ✅ FORMAT DE PERÍODE VÀLID")
                
                # Mostrar totes les cel·les d'aquesta fila
                for idx, cell in enumerate(cells[:11]):
                    text = cell.get_text(strip=True)
                    write_log(f"   Columna {idx}: '{text}'")
                
                # Verificar si té dades vàlides
                dades_valides = False
                for idx in range(1, 11):
                    text = cells[idx].get_text(strip=True)
                    if text and text != '(s/d)':
                        dades_valides = True
                        break
                
                if dades_valides:
                    write_log(f"   🎯 TE DADES VÀLIDES!")
                    
                    # Llegir les 11 columnes
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
                    write_log(f"      DVM: '{dvm}' | VVX: '{vvx}' | PM: '{pm}' | RS: '{rs}'")
                    
                    # Convertir a números
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
                    
                    # Ajustar període
                    periode_ajustat = ajustar_periode(periode)
                    
                    write_log(f"   ✅ RETORNANT DADES VÀLIDES")
                    return {
                        'periode': periode_ajustat,
                        'tm': tm_num, 'tx': tx_num, 'tn': tn_num,
                        'hr': hr_num, 'ppt': ppt_num, 'vvm': vvm_num,
                        'dvm': dvm_num, 'vvx': vvx_num, 'pm': pm_num,
                        'rs': rs_num
                    }
                else:
                    write_log(f"   ❌ NO TE DADES VÀLIDES - Cercant anterior...")
            else:
                write_log(f"   ❌ FORMAT DE PERÍODE INVÀLID - Cercant anterior...")
        
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
    
    dades = get_meteo_data()
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES")
        write_log("💤 NO S'ACTUALITZA RSS")
        return False
    
    write_log("✅ DADES OBTINGUDES - GENERANT RSS")
    
    titol = (
        f"[CAT] Actualitzat {current_time} | {dades['periode']} | "
        f"TM:{dades['tm']}°C | TX:{dades['tx']}°C | TN:{dades['tn']}°C | "
        f"HR:{dades['hr']}% | PPT:{dades['ppt']}mm | VVM:{dades['vvm']}km/h | "
        f"DVM:{dades['dvm']}° | VVX:{dades['vvx']}km/h | PM:{dades['pm']}hPa | RS:{dades['rs']}W/m2 | "
        f"[GB] Updated {current_time} | {dades['periode']} | "
        f"TM:{dades['tm']}°C | TX:{dades['tx']}°C | TN:{dades['tn']}°C | "
        f"HR:{dades['hr']}% | PPT:{dades['ppt']}mm | VVM:{dades['vvm']}km/h | "
        f"DVM:{dades['dvm']}° | VVX:{dades['vvx']}km/h | PM:{dades['pm']}hPa | RS:{dades['rs']}W/m2"
    )
    
    write_log(f"📝 Títol generat ({len(titol)} caràcters)")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat RSS</title>
  <link>https://www.meteo.cat</link>
  <description>Automated meteorological data - Dades meteorològiques automàtiques</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    with open('meteo.rss', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    write_log("✅ RSS guardat a 'meteo.rss'")
    
    return True

if __name__ == "__main__":
    # Netejar log anterior
    if os.path.exists('debug.log'):
        os.remove('debug.log')
    
    with open('debug.log', 'w', encoding='utf-8') as f:
        f.write("=== DEBUG LOG METEO.CAT - ESTACIÓ XJ (GIRONA) ===\n")
        f.write(f"Inici: {datetime.now()}\n")
        f.write("="*60 + "\n")
    
    write_log("🚀 SCRIPT INICIAT - ESTACIÓ XJ (GIRONA)")
    write_log(f"🐍 Versió Python: {sys.version}")
    
    exit = generar_rss()
    
    if exit:
        write_log("🎉 ÈXIT - RSS ACTUALITZAT")
    else:
        write_log("💤 FALLADA - NO S'HA ACTUALITZAT RSS")
    
    write_log("="*60)
    write_log("🏁 FI DE L'EXECUCIÓ")
    
    sys.exit(0 if exit else 1)
