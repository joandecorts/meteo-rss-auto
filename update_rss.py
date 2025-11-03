import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import re
import sys
import os

def write_log(message):
    """Escriu un missatge al log i també el mostra per pantalla"""
    print(message)
    with open('debug.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def diagnostica_taula():
    try:
        write_log("="*60)
        write_log("🔍 DIAGNÒSTIC DETALLAT DE LA TAULA")
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
            return False
            
        write_log("✅ Taula 'tblperiode' trobada")
            
        rows = table.find_all('tr')
        write_log(f"📊 Files a la taula: {len(rows)}")
        
        if not rows:
            write_log("❌ La taula no té files")
            return False
        
        # Analitzem la primera fila (capçalera) en detall
        write_log("\n" + "="*50)
        write_log("📋 ANALITZANT CAPÇALERA (fila 0)")
        write_log("="*50)
        
        cells_row0 = rows[0].find_all(['th', 'td'])
        write_log(f"Nombre d'elements (th/td) a la fila 0: {len(cells_row0)}")
        for i, cell in enumerate(cells_row0):
            write_log(f"  Element {i}: etiqueta='{cell.name}', text='{cell.get_text(strip=True)}'")
        
        # Analitzem les primeres 5 files de dades
        write_log("\n" + "="*50)
        write_log("📊 ANALITZANT PRIMERES 5 FILES DE DADES")
        write_log("="*50)
        
        for i in range(1, min(6, len(rows))):
            write_log(f"\n--- FILA {i} ---")
            cells = rows[i].find_all(['td', 'th'])  # Busquem tant td com th per si de cas
            write_log(f"Nombre d'elements (td/th) a la fila {i}: {len(cells)}")
            
            for j, cell in enumerate(cells):
                write_log(f"  Element {j}: etiqueta='{cell.name}', text='{cell.get_text(strip=True)}'")
        
        # Analitzem les últimes 5 files de dades
        write_log("\n" + "="*50)
        write_log("📊 ANALITZANT ÚLTIMES 5 FILES DE DADES")
        write_log("="*50)
        
        start_index = max(1, len(rows) - 5)
        for i in range(start_index, len(rows)):
            write_log(f"\n--- FILA {i} ---")
            cells = rows[i].find_all(['td', 'th'])
            write_log(f"Nombre d'elements (td/th) a la fila {i}: {len(cells)}")
            
            for j, cell in enumerate(cells):
                write_log(f"  Element {j}: etiqueta='{cell.name}', text='{cell.get_text(strip=True)}'")
        
        return True
        
    except Exception as e:
        write_log(f"❌ ERROR durant el diagnòstic: {str(e)}")
        import traceback
        write_log(f"TRACEBACK: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # Netejar log anterior
    if os.path.exists('debug.log'):
        os.remove('debug.log')
    
    with open('debug.log', 'w', encoding='utf-8') as f:
        f.write("=== DIAGNÒSTIC TAULA METEO.CAT ===\n")
        f.write(f"Data: {datetime.now()}\n")
        f.write("Estació: XJ (Girona)\n")
        f.write("="*60 + "\n")
    
    write_log("🚀 INICIANT DIAGNÒSTIC...")
    
    exit = diagnostica_taula()
    
    if exit:
        write_log("\n🎉 DIAGNÒSTIC COMPLETAT")
    else:
        write_log("\n💤 DIAGNÒSTIC FALLIDA")
    
    write_log("="*60)
    write_log("🏁 FI DEL DIAGNÒSTIC")
    
    sys.exit(0)
