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
        
        # INVESTIGACIÓ: Mostrar primeres i últimes files
        write_log("\n🔍 INVESTIGANT ESTRUCTURA DE LA TAULA:")
        
        # Mostrar les primeres 3 files
        write_log("\n📋 PRIMERES 3 FILES:")
        for i in range(0, min(3, len(rows))):
            cells = rows[i].find_all(['th', 'td'])
            write_log(f"Fila {i}: {len(cells)} cel·les")
            for j, cell in enumerate(cells):
                write_log(f"   Columna {j}: '{cell.get_text(strip=True)}'")
        
        # Mostrar les últimes 3 files
        write_log("\n📋 ÚLTIMES 3 FILES:")
        for i in range(max(0, len(rows)-3), len(rows)):
            cells = rows[i].find_all(['th', 'td'])
            write_log(f"Fila {i}: {len(cells)} cel·les")
            for j, cell in enumerate(cells):
                write_log(f"   Columna {j}: '{cell.get_text(strip=True)}'")
        
        # Ara cercarem files amb períodes vàlids
        write_log("\n🔍 CERCANT PERÍODES VÀLIDS A TOTES LES FILES...")
        
        for i in range(1, len(rows)):
            cells = rows[i].find_all('td')
            if len(cells) < 10:
                continue
                
            periode = cells[0].get_text(strip=True)
            
            if re.match(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', periode):
                write_log(f"✅ TROBAT PERÍODE VÀLID a fila {i}: {periode}")
                write_log(f"   Número de cel·les: {len(cells)}")
                for idx, cell in enumerate(cells):
                    write_log(f"   Columna {idx}: '{cell.get_text(strip=True)}'")
        
        write_log("❌ Cap període vàlid trobat?")
        return None
        
    except Exception as e:
        write_log(f"❌ ERROR CRÍTIC a get_meteo_data(): {str(e)}")
        import traceback
        write_log(f"TRACEBACK: {traceback.format_exc()}")
        return None

def generar_rss():
    write_log("\n" + "="*60)
    write_log("🚀 INICIANT GENERACIÓ RSS")
    
    dades = get_meteo_data()
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES")
        write_log("💤 NO S'ACTUALITZA RSS")
        return False
    
    write_log("✅ DADES OBTINGUDES - GENERANT RSS")
    return True

if __name__ == "__main__":
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
    
    sys.exit(0)
