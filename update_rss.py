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
    with open('debug_fornells.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def debug_html_structure(soup):
    """Analitza tota l'estructura HTML per trobar taules"""
    write_log("\n🔍 ANALITZANT ESTRUCTURA HTML COMPLETA...")
    
    # Busquem TOTES les taules
    all_tables = soup.find_all('table')
    write_log(f"📊 Total taules trobades: {len(all_tables)}")
    
    for i, table in enumerate(all_tables):
        write_log(f"\n--- TAULA {i} ---")
        write_log(f"   Classes: {table.get('class', ['No classes'])}")
        write_log(f"   ID: {table.get('id', 'No ID')}")
        
        # Mirem les primeres files per entendre l'estructura
        rows = table.find_all('tr')[:3]
        write_log(f"   Files totals: {len(table.find_all('tr'))}")
        write_log(f"   Mostrant primeres {len(rows)} files:")
        
        for j, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            write_log(f"     Fila {j}: {len(cells)} cel·les")
            for k, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                write_log(f"       Cel·la {k}: '{text}'")

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
        
        # DEBUG: Analitzem tota l'estructura
        debug_html_structure(soup)
        
        # Provem diferents estratègies per trobar la taula
        tables_found = []
        
        # Estratègia 1: Buscar per classe específica
        table = soup.find('table', {'class': 'tblperiode'})
        if table:
            write_log("✅ TAULA TROBADA per classe 'tblperiode'")
            tables_found.append(('tblperiode', table))
        
        # Estratègia 2: Buscar per qualsevol taula que sembli de dades
        all_tables = soup.find_all('table')
        for tbl in all_tables:
            rows = tbl.find_all('tr')
            if len(rows) > 2:  # Si té més de 2 files, potser és la taula de dades
                first_row_cells = rows[0].find_all(['td', 'th'])
                if len(first_row_cells) > 5:  # Si té suficients columnes
                    tables_found.append(('generic', tbl))
        
        write_log(f"🎯 Taules candidates trobades: {len(tables_found)}")
        
        if not tables_found:
            write_log("❌ No s'ha trobat cap taula de dades")
            return None
        
        # Processem la primera taula vàlida
        table_name, table = tables_found[0]
        write_log(f"🔍 Processant taula: {table_name}")
            
        rows = table.find_all('tr')
        write_log(f"📊 Files a la taula: {len(rows)}")
        
        if not rows:
            write_log("❌ La taula no té files")
            return None
        
        write_log("\n🔍 CERCANT PERÍODE MÉS RECENT AMB DADES VÀLIDES...")
        
        for i in range(len(rows)):
            cells = rows[i].find_all(['td', 'th'])
            write_log(f"\n--- ANALITZANT FILA {i} ---")
            write_log(f"   Cel·les (td+th): {len(cells)}")
            
            if len(cells) < 6:  # Reduïm el mínim requerit
                write_log(f"   ❌ Només té {len(cells)} columnes - massa poques")
                continue
                
            # Mirem el contingut de les primeres cel·les
            for idx in range(min(3, len(cells))):
                text = cells[idx].get_text(strip=True)
                write_log(f"   Columna {idx}: '{text}'")
            
            periode = cells[0].get_text(strip=True)
            write_log(f"   Període: '{periode}'")
            
            # Pattern més flexible per períodes
            if re.match(r'\d{1,2}[:\.]\d{2}', periode.replace('-', '').replace(' ', '')):
                write_log(f"   ✅ FORMAT DE PERÍODE VÀLID")
                
                dades_valides = False
                for idx in range(1, min(len(cells), 6)):  # Mirem les primeres 5 columnes de dades
                    text = cells[idx].get_text(strip=True)
                    if text and text != '(s/d)' and text != '-':
                        dades_valides = True
                        break
                
                if dades_valides:
                    write_log(f"   🎯 TE DADES VÀLIDES - PROCESSANT...")
                    
                    # Extracció de dades amb índexs flexibles
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
                        'periode': periode_ajustat,
                        'tm': tm_num, 'tx': tx_num, 'tn': tn_num,
                        'hr': hr_num, 'ppt': ppt_num
                    }
                else:
                    write_log(f"   ❌ NO TE DADES VÀLIDES - Cercant fila anterior...")
            else:
                write_log(f"   ❌ FORMAT DE PERÍODE INVÀLID - Cercant fila anterior...")
        
        write_log("❌ CAP FILA TE DADES VÀLIDES")
        return None
        
    except Exception as e:
        write_log(f"❌ ERROR CRÍTIC a get_meteo_data_fornells(): {str(e)}")
        import traceback
        write_log(f"TRACEBACK: {traceback.format_exc()}")
        return None

def ajustar_periode(periode_str):
    try:
        write_log(f"   🕒 Ajustant període: {periode_str}")
        # Pattern més flexible
        match = re.match(r'(\d{1,2})[:\.](\d{2})\s*-\s*(\d{1,2})[:\.](\d{2})', periode_str)
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
