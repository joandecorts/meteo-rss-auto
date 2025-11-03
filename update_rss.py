import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import re
import sys

def write_log(message):
    """Escriu un missatge al log i també el mostra per pantalla"""
    print(message)
    with open('debug.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def get_meteo_data():
    try:
        # Netejar el fitxer de log anterior
        with open('debug.log', 'w', encoding='utf-8') as f:
            f.write("=== DEBUG LOG METEO.CAT ===\n")
            f.write(f"Hora inici: {datetime.now()}\n")
        
        write_log("🌐 Connectant a Meteo.cat...")
        url = "https://www.meteo.cat/observacions/xema/dades?codi=Z6"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        write_log("✅ Connexió exitosa")
        write_log(f"🔗 URL: {url}")
        write_log(f"📄 Mida resposta: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar TOTES les taules per si ha canviat
        tables = soup.find_all('table')
        write_log(f"📊 Taules trobades: {len(tables)}")
        
        for idx, table in enumerate(tables):
            write_log(f"  Taula {idx}: classes = {table.get('class', ['No class'])}")
        
        target_table = None
        for table in tables:
            if 'tblperiode' in table.get('class', []):
                target_table = table
                break
        
        if not target_table and tables:
            write_log("⚠️  No s'ha trobat 'tblperiode', provant amb la primera taula")
            target_table = tables[0]
            
        if not target_table:
            write_log("❌ NO HI HA TAULES A LA PÀGINA")
            return None
            
        rows = target_table.find_all('tr')
        write_log(f"📊 Files a la taula: {len(rows)}")
        
        # Mostrar les CAPÇALERES per veure l'estructura
        if rows:
            header_cells = rows[0].find_all(['th', 'td'])
            header_texts = [cell.get_text(strip=True) for cell in header_cells]
            write_log(f"📋 CAPÇALERES: {header_texts}")
            write_log(f"📋 Número de capçaleres: {len(header_texts)}")
        
        # Analitzar les 10 files més recents
        write_log("\n🔍 ANALITZANT LES 10 FILES MÉS RECENTS:")
        files_analitzades = 0
        
        for i in range(max(1, len(rows)-10), len(rows)):
            files_analitzades += 1
            cells = rows[i].find_all('td')
            
            write_log(f"\n--- FILA {i} ---")
            write_log(f"   Número de cel·les: {len(cells)}")
            
            if cells:
                periode = cells[0].get_text(strip=True)
                write_log(f"   Període: '{periode}'")
                
                # Mostrar TOTES les cel·les d'aquesta fila
                for idx, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    write_log(f"   Columna {idx}: '{text}'")
                
                # Verificar si és un període vàlid
                if re.match(r'\d{1,2}:\d{2}\s*-\s*(\d{1,2}:\d{2})?', periode):
                    write_log(f"✅ FORMAT DE PERÍODE VÀLID: {periode}")
                    
                    # Verificar si té dades vàlides
                    dades_valides = False
                    for idx in range(1, min(11, len(cells))):
                        text = cells[idx].get_text(strip=True)
                        if text and text != '(s/d)':
                            dades_valides = True
                            break
                    
                    if dades_valides:
                        write_log(f"🎯 FILA {i} TE DADES VÀLIDES!")
                        
                        # Llegir les 11 columnes
                        tm = cells[1].get_text(strip=True) if len(cells) > 1 else "N/A"
                        tx = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
                        tn = cells[3].get_text(strip=True) if len(cells) > 3 else "N/A"
                        hr = cells[4].get_text(strip=True) if len(cells) > 4 else "N/A"
                        ppt = cells[5].get_text(strip=True) if len(cells) > 5 else "N/A"
                        vvm = cells[6].get_text(strip=True) if len(cells) > 6 else "N/A"
                        dvm = cells[7].get_text(strip=True) if len(cells) > 7 else "N/A"
                        vvx = cells[8].get_text(strip=True) if len(cells) > 8 else "N/A"
                        pm = cells[9].get_text(strip=True) if len(cells) > 9 else "N/A"
                        rs = cells[10].get_text(strip=True) if len(cells) > 10 else "N/A"
                        
                        write_log("📊 DADES EXTRAÏDES:")
                        write_log(f"   TM: '{tm}' | TX: '{tx}' | TN: '{tn}'")
                        write_log(f"   HR: '{hr}' | PPT: '{ppt}' | VVM: '{vvm}'")
                        write_log(f"   DVM: '{dvm}' | VVX: '{vvx}' | PM: '{pm}' | RS: '{rs}'")
                        
                        # Convertir a números
                        def a_numero(text, default=0.0):
                            if not text or text == '(s/d)' or text == 'N/A':
                                return default
                            try:
                                return float(text.replace(',', '.'))
                            except:
                                return default
                        
                        # Ajustar període
                        periode_ajustat = ajustar_periode(periode)
                        
                        return {
                            'periode': periode_ajustat,
                            'tm': a_numero(tm),
                            'tx': a_numero(tx, a_numero(tm)),
                            'tn': a_numero(tn, a_numero(tm)),
                            'hr': a_numero(hr),
                            'ppt': a_numero(ppt),
                            'vvm': a_numero(vvm),
                            'dvm': a_numero(dvm),
                            'vvx': a_numero(vvx),
                            'pm': a_numero(pm),
                            'rs': a_numero(rs)
                        }
                    else:
                        write_log(f"❌ FILA {i} NO TE DADES VÀLIDES")
                else:
                    write_log(f"❌ FORMAT DE PERÍODE INVÀLID: {periode}")
            else:
                write_log("❌ FILA SENSE CEL·LES")
        
        write_log(f"\n📝 RESUM: S'han analitzat {files_analitzades} files")
        write_log("❌ CAP FILA TE DADES VÀLIDES")
        return None
        
    except Exception as e:
        write_log(f"❌ ERROR CRÍTIC: {str(e)}")
        import traceback
        write_log(f"TRACEBACK: {traceback.format_exc()}")
        return None

def ajustar_periode(periode_str):
    """Ajusta període TU (UTC) a hora local"""
    try:
        match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}:\d{2})?', periode_str)
        if match:
            hora_inici = int(match.group(1))
            minut_inici = int(match.group(2))
            # Alguns períodes poden no tenir hora fi
            if match.group(3):
                hora_fi = int(match.group(3).split(':')[0])
                minut_fi = int(match.group(3).split(':')[1])
            else:
                # Si no hi ha hora fi, assumim 30 minuts després
                hora_fi = (hora_inici + 1) if minut_inici >= 30 else hora_inici
                minut_fi = 0 if minut_inici >= 30 else 30
            
            # Determinar diferència horària
            cet = pytz.timezone('CET')
            ara_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            ara_cet = ara_utc.astimezone(cet)
            
            es_dst = ara_cet.dst() != timedelta(0)
            hores_diferencia = 2 if es_dst else 1
            
            hora_inici_ajustada = (hora_inici + hores_diferencia) % 24
            hora_fi_ajustada = (hora_fi + hores_diferencia) % 24
            
            periode_ajustat = f"{hora_inici_ajustada:02d}:{minut_inici:02d}-{hora_fi_ajustada:02d}:{minut_fi:02d}"
            write_log(f"🕒 PERÍODE AJUSTAT: {periode_str} TU → {periode_ajustat} {'CEST' if es_dst else 'CET'}")
            return periode_ajustat
            
    except Exception as e:
        write_log(f"❌ Error ajustant període: {e}")
    
    return periode_str

def generar_rss():
    write_log("\n" + "="*50)
    write_log("🚀 INICIANT GENERACIÓ RSS")
    
    dades = get_meteo_data()
    
    # Hora actual
    cet = pytz.timezone('CET')
    ara = datetime.now(cet)
    hora_actual = ara.strftime("%H:%M")
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES - NO S'ACTUALITZA RSS")
        return False
    
    write_log("✅ DADES OBTINGUDES CORRECTAMENT")
    
    # Crear títol amb les 11 dades
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
    
    write_log(f"📝 TÍTOL GENERAT: {titol}")
    
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
    
    # Guardar arxiu RSS
    with open('meteo.rss', 'w', encoding='utf-8') as f:
        f.write(contingut_rss)
    
    write_log("✅ RSS ACTUALITZAT CORRECTAMENT")
    write_log(f"💾 Fitxer 'meteo.rss' guardat")
    write_log(f"📝 Fitxer 'debug.log' amb informació detallada")
    
    return True

if __name__ == "__main__":
    write_log("="*60)
    write_log("🚀 INICIANT SCRIPT METEO.CAT RSS")
    write_log(f"⏰ Data/hora: {datetime.now()}")
    write_log("="*60)
    
    exit = generar_rss()
    if exit:
        write_log("🎉 COMPLETAT - RSS ACTUALITZAT")
    else:
        write_log("💤 NO S'HA ACTUALITZAT - Sense dades vàlides")
    
    write_log("="*60)
    write_log("🏁 FI DE L'EXECUCIÓ")
    write_log("="*60)
    
    sys.exit(0)
