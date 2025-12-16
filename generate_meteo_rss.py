#!/usr/bin/env python3
"""
Script per generar el ticker HTML a partir del fitxer RSS que ja tens.
Versió simplificada - només processa Girona i Fornells de la Selva.
"""

import urllib.request
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys

# ============================================================================
# FUNCIONS AUXILIARS PER EXTREURE DADES
# ============================================================================

def extreure_dades_estacio(title_text: str, nom_estacio: str, codi_estacio: str) -> Dict[str, Any]:
    """Extreu totes les dades meteorològiques d'un títol d'estació."""
    
    station_data = {
        'name': nom_estacio,
        'code': codi_estacio,
        # Temperatures
        'temp_actual': None,
        'temp_maxima': None,
        'temp_minima': None,
        # Humitat i precipitació
        'humitat': None,
        'precipitacio': '0.0',
        # Vent
        'vent': None,
        'vent_direccio': None,
        'vent_maxim': None,
        # Pressió i radiació
        'pressio': None,
        'radiacio': None,
        # Dades addicionals
        'periode': None,
        'actualitzacio': None
    }
    
    # EXTREURE TOTES LES DADES METEOROLÒGIQUES DEL TÍTOL
    
    # Temperatura Actual (busquem 'Actual:' o 'Temp. Mitjana:')
    temp_actual_match = re.search(r'(?:Actual|Temp\. Mitjana):\s*([\d.-]+)°C', title_text)
    if temp_actual_match:
        station_data['temp_actual'] = temp_actual_match.group(1)
    
    # Temperatura Màxima
    temp_maxima_match = re.search(r'(?:Temp\. Màxima|Màxima):\s*([\d.-]+)°C', title_text)
    if temp_maxima_match:
        station_data['temp_maxima'] = temp_maxima_match.group(1)
    
    # Temperatura Mínima
    temp_minima_match = re.search(r'(?:Temp\. Mínima|Mínima):\s*([\d.-]+)°C', title_text)
    if temp_minima_match:
        station_data['temp_minima'] = temp_minima_match.group(1)
    
    # Humitat
    humitat_match = re.search(r'Humitat:\s*([\d.-]+)%', title_text)
    if humitat_match:
        station_data['humitat'] = humitat_match.group(1)
    
    # Precipitació
    precipitacio_match = re.search(r'Precipitació:\s*([\d.-]+)mm', title_text)
    if precipitacio_match:
        station_data['precipitacio'] = precipitacio_match.group(1)
    
    # Vent (mitjà)
    vent_match = re.search(r'(?:Vent|Vent mitjà):\s*([\d.-]+)km/h', title_text)
    if vent_match:
        station_data['vent'] = vent_match.group(1)
    
    # Direcció Vent
    vent_dir_match = re.search(r'(?:Dir\.Vent|Direcció vent):\s*([\d.-]+)°', title_text)
    if vent_dir_match:
        station_data['vent_direccio'] = vent_dir_match.group(1)
    
    # Vent Màxim
    vent_max_match = re.search(r'(?:Vent Màx|Ratxa màxima):\s*([\d.-]+)km/h', title_text)
    if vent_max_match:
        station_data['vent_maxim'] = vent_max_match.group(1)
    
    # Pressió
    pressio_match = re.search(r'Pressió:\s*([\d.-]+)hPa', title_text)
    if pressio_match:
        station_data['pressio'] = pressio_match.group(1)
    
    # Radiació
    radiacio_match = re.search(r'Radiació:\s*([\d.-]+)W/m²', title_text)
    if radiacio_match:
        station_data['radiacio'] = radiacio_match.group(1)
    
    # Període
    periode_match = re.search(r'Període:\s*([\d:\s-]+)', title_text)
    if periode_match:
        station_data['periode'] = periode_match.group(1).strip()
    
    # Actualització
    actualitzacio_match = re.search(r'Actualitzat:\s*([\d:]+)', title_text)
    if actualitzacio_match:
        station_data['actualitzacio'] = actualitzacio_match.group(1)
    
    return station_data

def obtenir_dades_del_rss(url_rss: str = 'https://joandecorts.github.io/meteo-rss-auto/meteo.rss') -> List[Dict[str, Any]]:
    """
    Llegeix el fitxer RSS i extreu les dades només de Girona i Fornells.
    Versió SIMPLIFICADA i ROBUSTA - ignora la resta d'ítems.
    """
    try:
        print(f"[INFO] Obtenint dades del RSS: {url_rss}")
        
        with urllib.request.urlopen(url_rss) as response:
            rss_content = response.read().decode('utf-8')
        
        print("[OK] RSS obtingut correctament")
        
        # Buscar DIRECTAMENT les dues estacions que ens interessen
        stations_data = []
        
        # Patró per trobar el títol COMPLET d'una estació (inclou totes les dades)
        # Busquem des del nom de l'estació fins al final del títol
        patron_estacio = r'<title>.*?({}).*?</title>'
        
        # Buscar Girona
        girona_patron = patron_estacio.format('Girona')
        girona_match = re.search(girona_patron, rss_content, re.IGNORECASE | re.DOTALL)
        if girona_match:
            titol_complet = girona_match.group(0)  # Tota la etiqueta <title>...</title>
            # Extreure només el contingut del títol (sense les etiquetes)
            titol_contingut_match = re.search(r'<title>(.*?)</title>', titol_complet, re.DOTALL)
            if titol_contingut_match:
                title_text = titol_contingut_match.group(1).strip()
                station_data = extreure_dades_estacio(title_text, "Girona", "XJ")
                if station_data:
                    stations_data.append(station_data)
                    print(f"[OK] Processada: Girona")
        
        # Buscar Fornells
        fornells_patron = patron_estacio.format('Fornells')
        fornells_match = re.search(fornells_patron, rss_content, re.IGNORECASE | re.DOTALL)
        if fornells_match:
            titol_complet = fornells_match.group(0)
            titol_contingut_match = re.search(r'<title>(.*?)</title>', titol_complet, re.DOTALL)
            if titol_contingut_match:
                title_text = titol_contingut_match.group(1).strip()
                station_data = extreure_dades_estacio(title_text, "Fornells de la Selva", "UO")
                if station_data:
                    stations_data.append(station_data)
                    print(f"[OK] Processada: Fornells de la Selva")
        
        # Informe del que s'ha trobat
        if stations_data:
            print(f"[OK] S'han trobat {len(stations_data)} estacions vàlides")
            for estacio in stations_data:
                print(f"  - {estacio['name']}: T={estacio.get('temp_actual', 'N/D')}°C, H={estacio.get('humitat', 'N/D')}%")
        else:
            print("[ERROR] No s'han trobat les estacions buscades al RSS")
            # DEBUG: Mostrar una mostra del RSS per veure què hi ha
            print("[DEBUG] Mostrant els primers 500 caràcters del RSS:")
            print(rss_content[:500])
        
        return stations_data
        
    except Exception as e:
        print(f"[ERROR] Obtenint dades del RSS: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []

# ============================================================================
# GENERACIÓ DE L'HTML (ADAPTADA PER A LES DADES DEL RSS)
# ============================================================================

def renderitzar_html(estacions: List[Dict[str, Any]]) -> str:
    """Genera el codi HTML del ticker a partir de les dades del RSS."""
    
    def fmt(val, unitat=''):
        """Formata un valor per a mostrar-lo."""
        if val is None:
            return 'N/D'
        try:
            # Intentar convertir a float per arrodonir
            num = float(val)
            if num.is_integer():
                return f'{int(num)}{unitat}'
            return f'{num:.1f}{unitat}'.rstrip('0').rstrip('.') + unitat
        except (ValueError, TypeError):
            return str(val) if val else 'N/D'
    
    hora_actual = datetime.now().strftime('%H:%M')
    data_actual = datetime.now().strftime('%d/%m/%Y')
    
    # Separar estacions per al ticker
    estacio1 = estacions[0] if len(estacions) > 0 else {}
    estacio2 = estacions[1] if len(estacions) > 1 else {}
    
    # Determinar noms per a les columnes del ticker
    nom_estacio1 = estacio1.get('name', 'GIRONA')
    nom_estacio2 = estacio2.get('name', 'FORNELLS DE LA SELVA')
    
    html = f'''<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticker Meteorològic</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{ margin: 0; padding: 0; background: #111; color: #eee; font-family: 'Segoe UI', sans-serif; overflow: hidden; }}
        .ticker {{ display: flex; background: linear-gradient(90deg, #1a3c5f, #2a2a2a); padding: 10px 20px; border-bottom: 3px solid #0cf; }}
        .estacio {{ flex: 1; padding: 0 20px; border-right: 1px solid #444; }}
        .estacio:last-child {{ border-right: none; }}
        .header {{ display: flex; align-items: center; margin-bottom: 8px; color: #0cf; }}
        .header i {{ margin-right: 10px; font-size: 1.2em; }}
        .dades {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
        .dada {{ background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; }}
        .etiqueta {{ font-size: 0.85em; color: #aaa; }}
        .valor {{ font-size: 1.4em; font-weight: bold; color: #fff; }}
        .unitat {{ font-size: 0.9em; color: #0cf; margin-left: 3px; }}
        .temps-actual {{ font-size: 0.9em; color: #8f8; margin-top: 5px; }}
        .timestamp {{ text-align: center; padding: 10px; color: #aaa; font-size: 0.9em; border-top: 1px solid #333; }}
        .fa-temperature-high {{ color: #ff6b6b; }}
        .fa-temperature-low {{ color: #4dabf7; }}
        .fa-tint {{ color: #339af0; }}
        .fa-wind {{ color: #a9e34b; }}
        .fa-compress-alt {{ color: #da77f2; }}
        .fa-sun {{ color: #ffd43b; }}
    </style>
</head>
<body>
    <div class="ticker">
        <!-- PRIMERA ESTACIÓ -->
        <div class="estacio">
            <div class="header">
                <i class="fas fa-map-marker-alt"></i>
                <h3>{nom_estacio1.upper()}</h3>
            </div>
            <div class="temps-actual">Període: {estacio1.get('periode', 'N/D')}</div>
            <div class="dades">
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Actual</div><div class="valor">{fmt(estacio1.get('temp_actual'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Màx</div><div class="valor">{fmt(estacio1.get('temp_maxima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-low"></i> Mín</div><div class="valor">{fmt(estacio1.get('temp_minima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-tint"></i> Humitat</div><div class="valor">{fmt(estacio1.get('humitat'), '')}<span class="unitat">%</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-cloud-rain"></i> Pluja</div><div class="valor">{fmt(estacio1.get('precipitacio'), '')}<span class="unitat">mm</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-wind"></i> Vent</div><div class="valor">{fmt(estacio1.get('vent'), '')}<span class="unitat">km/h</span></div></div>
            </div>
        </div>
        
        <!-- SEGONA ESTACIÓ (si existeix) -->
        <div class="estacio">
            <div class="header">
                <i class="fas fa-map-marker-alt"></i>
                <h3>{nom_estacio2.upper()}</h3>
            </div>
            <div class="temps-actual">Període: {estacio2.get('periode', 'N/D')}</div>
            <div class="dades">
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Actual</div><div class="valor">{fmt(estacio2.get('temp_actual'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Màx</div><div class="valor">{fmt(estacio2.get('temp_maxima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-low"></i> Mín</div><div class="valor">{fmt(estacio2.get('temp_minima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-tint"></i> Humitat</div><div class="valor">{fmt(estacio2.get('humitat'), '')}<span class="unitat">%</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-cloud-rain"></i> Pluja</div><div class="valor">{fmt(estacio2.get('precipitacio', 0), '')}<span class="unitat">mm</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-wind"></i> Vent</div><div class="valor">{fmt(estacio2.get('vent'), '')}<span class="unitat">km/h</span></div></div>
            </div>
        </div>
    </div>
    
    <div class="timestamp">
        <i class="far fa-clock"></i> Dades actualitzades a les {hora_actual} del {data_actual} |
        Font: <a href="https://meteo.cat" style="color:#4dabf7;">Servei Meteorològic de Catalunya</a> |
        Via: <a href="https://joandecorts.github.io/meteo-rss-auto/meteo.rss" style="color:#4dabf7;">RSS Automàtic</a>
    </div>
</body>
</html>'''
    return html

# ============================================================================
# EXECUCIÓ PRINCIPAL
# ============================================================================

def main():
    print("=" * 60)
    print("INICIANT GENERACIÓ DEL TICKER DES DEL RSS")
    print("=" * 60)
    
    # 1. OBTENIR DADES DEL RSS
    print("\n[1] Obtenint dades del RSS...")
    estacions = obtenir_dades_del_rss()
    
    if len(estacions) < 2:
        print(f"[WARNING] Només s'han trobat {len(estacions)} estacions (esperades: 2)")
        if len(estacions) == 0:
            print("[ERROR] No s'han pogut obtenir dades. Surtint.", file=sys.stderr)
            sys.exit(1)
    
    print(f"[OK] Obtingudes {len(estacions)} estacions")
    
    # 2. GUARDAR DADES EN FORMAT JSON (opcional, per a càrrega ràpida)
    data_avui = datetime.now().strftime('%Y-%m-%d')
    nom_fitxer_cache = f"meteo_cache_rss_{data_avui}.json"
    
    with open(nom_fitxer_cache, 'w', encoding='utf-8') as f:
        json.dump({
            'data_processament': datetime.now().isoformat(),
            'estacions': estacions,
            'total_estacions': len(estacions)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Dades guardades a: {nom_fitxer_cache}")
    
    # 3. GENERAR HTML
    print("[2] Generant HTML del ticker...")
    html_final = renderitzar_html(estacions)
    
    # 4. ESCRIURE FITXER
    output_file = Path("index.html")
    output_file.write_text(html_final, encoding='utf-8')
    
    print(f"[OK] HTML generat: {output_file.resolve()}")
    print("\n✅ TICKER ACTUALITZAT CORRECTAMENT")
    print("=" * 60)

if __name__ == "__main__":
    main()
