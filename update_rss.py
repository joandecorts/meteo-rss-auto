import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys

def get_meteo_data():
    try:
        print("🌐 Connectant a Meteo.cat...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("✅ Connexió exitosa")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'tblperiode'})
        if not table:
            print("❌ No s'ha trobat la taula")
            return None
            
        rows = table.find_all('tr')
        print(f"📊 Files trobades: {len(rows)}")
        
        # Recórrer des de l'última fila (més recent) fins a la primera
        for i in range(len(rows)-1, 0, -1):
            cells = rows[i].find_all('td')
            
            if len(cells) >= 11:  # Assegurar que tenim les 11 columnes
                periode = cells[0].get_text(strip=True)
                
                # Verificar si és un període vàlid
                if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                    print(f"\n🔍 ANALITZANT PERÍODE: {periode}")
                    
                    # LLEGIR LES 11 COLUMNES EN L'ORDRE EXACTE
                    tm = cells[1].get_text(strip=True)   # TM
                    tx = cells[2].get_text(strip=True)   # TX
                    tn = cells[3].get_text(strip=True)   # TN
                    hr = cells[4].get_text(strip=True)   # HR
                    ppt = cells[5].get_text(strip=True)  # PPT
                    vvm = cells[6].get_text(strip=True)  # VVM
                    dvm = cells[7].get_text(strip=True)  # DVM
                    vvx = cells[8].get_text(strip=True)  # VVX
                    pm = cells[9].get_text(strip=True)   # PM
                    rs = cells[10].get_text(strip=True)  # RS
                    
                    print("📊 LES 11 DADES EN BRUT:")
                    print(f"   Període: {periode}")
                    print(f"   TM: '{tm}' | TX: '{tx}' | TN: '{tn}'")
                    print(f"   HR: '{hr}' | PPT: '{ppt}' | VVM: '{vvm}'")
                    print(f"   DVM: '{dvm}' | VVX: '{vvx}' | PM: '{pm}' | RS: '{rs}'")
                    
                    # Verificar si hi ha dades vàlides (no buides ni "s/d")
                    dades_valides = any([
                        tm and tm != '(s/d)', tx and tx != '(s/d)', tn and tn != '(s/d)',
                        hr and hr != '(s/d)', ppt and ppt != '(s/d)', vvm and vvm != '(s/d)',
                        dvm and dvm != '(s/d)', vvx and vvx != '(s/d)', pm and pm != '(s/d)',
                        rs and rs != '(s/d)'
                    ])
                    
                    if dades_valides:
                        print("✅ PERÍODE AMB DADES VÀLIDES - PROCESSANT...")
                        
                        # Convertir tots els valors a números
                        def a_numero(text, default=0.0):
                            if not text or text == '(s/d)':
                                return default
                            try:
                                return float(text.replace(',', '.'))
                            except:
                                return default
                        
                        # Aplicar conversions a les 11 dades
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
                        
                        # Ajustar període TU a hora local
                        periode_ajustat = ajustar_periode(periode)
                        
                        return {
                            'periode': periode_ajustat,
                            'tm': tm_num, 'tx': tx_num, 'tn': tn_num,
                            'hr': hr_num, 'ppt': ppt_num, 'vvm': vvm_num,
                            'dvm': dvm_num, 'vvx': vvx_num, 'pm': pm_num,
                            'rs': rs_num
                        }
                    else:
                        print("❌ PERÍODE SENSE DADES - CERCANT ANTERIOR...")
                        continue
        
        print("❌ No s'ha trobat cap període amb dades vàlides")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def ajustar_periode(periode_str):
    """Ajusta període TU (UTC) a hora local"""
    try:
        match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', periode_str)
        if match:
            hora_inici = int(match.group(1))
            minut_inici = int(match.group(2))
            hora_fi = int(match.group(3))
            minut_fi = int(match.group(4))
            
            # Determinar diferència horària
            cet = pytz.timezone('CET')
            ara_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            ara_cet = ara_utc.astimezone(cet)
            
            es_dst = ara_cet.dst() != timedelta(0)
            hores_diferencia = 2 if es_dst else 1
            
            hora_inici_ajustada = (hora_inici + hores_diferencia) % 24
            hora_fi_ajustada = (hora_fi + hores_diferencia) % 24
            
            periode_ajustat = f"{hora_inici_ajustada:02d}:{minut_inici:02d}-{hora_fi_ajustada:02d}:{minut_fi:02d}"
            print(f"🕒 PERÍODE AJUSTAT: {periode_str} TU → {periode_ajustat} {'CEST' if es_dst else 'CET'}")
            return periode_ajustat
            
    except Exception as e:
        print(f"❌ Error ajustant període: {e}")
    
    return periode_str

def generar_rss():
    dades = get_meteo_data()
    
    # Hora actual
    cet = pytz.timezone('CET')
    ara = datetime.now(cet)
    hora_actual = ara.strftime("%H:%M")
    
    if not dades:
        print("❌ No s'han pogut obtenir dades - NO s'actualitza RSS")
        return False
    
    # Crear títol amb les 11 dades en l'ordre exacte
    titol = (
        f"[CAT] Actualitzat {hora_actual} | {dades['periode']} | "
        f"TM:{dades['tm']}°C | TX:{dades['tx']}°C | TN:{dades['tn']}°C | "
        f"HR:{dades['hr']}% | PPT:{dades['ppt']}mm | VVM:{dades['vvm']}km/h | "
        f"DVM:{dades['dvm']}° | VVX:{dades['vvx']}km/h | PM:{dades['pm']}hPa | RS:{dades['rs']}W/m2 | "
        f"[GB] Updated {hora_actual} | {dades['periode']} | "
        f"TM:{dades['tm']}°C | TX:{dades['tx']}°C | TN:{dades['tn']}°C | "
        f"HR:{dades['hr']}% | PPT:{dades['ppt']}mm | VVM:{dades['vvm']}km/h | "
        f"DVM:{dades['dvm']}° | VVX:{dades['vvx']}km/h | PM:{dades['pm']}hPa | RS:{dades['rs']}W/m2"
    )
    
    # Generar RSS
    contingut_rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat RSS</title>
  <link>https://www.meteo.cat</link>
  <description>Automated meteorological data - Dades meteorològiques automàtiques</description>
  <lastBuildDate>{ara.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat</link>
    <pubDate>{ara.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    # Guardar arxiu
    with open('meteo.rss', 'w', encoding='utf-8') as f:
        f.write(contingut_rss)
    
    print("✅ RSS ACTUALITZAT CORRECTAMENT AMB LES 11 DADES")
    return True

if __name__ == "__main__":
    print("🚀 Iniciant actualització RSS...")
    exit = generar_rss()
    if exit:
        print("🎉 COMPLETAT - RSS ACTUALITZAT")
    else:
        print("💤 NO S'HA ACTUALITZAT - Sense dades vàlides")
    sys.exit(0)
