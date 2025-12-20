#!/usr/bin/env python3
"""
Script principal per generar l'HTML del ticker meteorològic.
Actualitza les dades de Girona (XJ) i Fornells de la Selva (UO).
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# ============================================================================
# CONFIGURACIÓ I FUNCIONS AUXILIARS
# ============================================================================

def obtenir_dades_estacio(codi_estacio: str, cache_file_prefix: str = "daily_cache") -> Optional[Dict[str, Any]]:
    """
    Obté i processa les dades d'una estació XEMA de Meteo.cat.
    Retorna un diccionari amb les dades actuals, màximes, mínimes i pluja acumulada.
    
    Args:
        codi_estacio: Codi de l'estació (ex: 'XJ', 'UO').
        cache_file_prefix: Prefix per al fitxer JSON de cache diari.
    
    Returns:
        Diccionari amb les dades o None en cas d'error.
    """
    base_url = "https://www.meteo.cat/observacions/xema/dades"
    url = f"{base_url}?codi={codi_estacio}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. LOCALITZAR LA TAULA CRÍTICA
        taula = None
        for table in soup.find_all('table'):
            if table.find('th', string='PeríodeTU'):
                taula = table
                break
        
        if not taula:
            print(f"[ERROR] No s'ha trobat la taula de dades per a {codi_estacio}", file=sys.stderr)
            return None
        
        # 2. MAPEJAR ELS TÍTOLS DE LES COLUMNES
        fila_capsalera = taula.find('tr')
        capsaleres = [th.get_text(strip=True) for th in fila_capsalera.find_all(['th', 'td'])]
        index_columna = {nom: idx for idx, nom in enumerate(capsaleres)}
        
        # 3. DEFINIR LES COLUMNES QUE ENS INTERESSEN
        columnes_a_extreure = [
            ('PeríodeTU', 'periode', 'text'),
            ('TM°C', 'tm_actual', 'float'),
            ('TX°C', 'tx', 'float'),
            ('TN°C', 'tn', 'float'),
            ('HRM%', 'humitat', 'float'),
            ('PPTmm', 'pluja', 'float'),
            ('VVM (10 m)km/h', 'vent_vel_mitjana', 'float'),
            ('DVM (10 m)graus', 'vent_dir_mitjana', 'float'),
            ('VVX (10 m)km/h', 'vent_vel_maxima', 'float'),
            ('PMhPa', 'pressio', 'float'),
            ('RSW/m2', 'radiacio', 'float')
        ]
        
        # 4. RECOLLIR TOTES LES FILES DE DADES DEL DIA
        files_dades = []
        for fila in taula.find_all('tr')[1:]:
            cel·les = fila.find_all(['td', 'th'])
            if len(cel·les) != len(capsaleres):
                continue
            
            fila_dict = {'_raw_cells': [c.get_text(strip=True) for c in cel·les]}
            
            for nom_col_html, clau, tipus in columnes_a_extreure:
                if nom_col_html in index_columna:
                    idx = index_columna[nom_col_html]
                    valor_text = cel·les[idx].get_text(strip=True)
                    
                    if valor_text in ('(s/d)', '', '-', 'N/D'):
                        valor = None
                    else:
                        try:
                            if tipus == 'float':
                                valor = float(valor_text)
                            else:
                                valor = valor_text
                        except ValueError:
                            valor = valor_text
                    fila_dict[clau] = valor
                else:
                    fila_dict[clau] = None
            
            if fila_dict.get('periode'):
                files_dades.append(fila_dict)
        
        if not files_dades:
            print(f"[ERROR] No s'han trobat dades vàlides per a {codi_estacio}", file=sys.stderr)
            return None
        
        # 5. OBTENCIÓ DE L'ÚLTIM PERÍODE VÀLID (Ítems 1, 2)
        dades_actuals = None
        for fila in reversed(files_dades):
            if fila.get('tm_actual') is not None:
                dades_actuals = fila
                break
        
        if not dades_actuals:
            dades_actuals = files_dades[-1]
        
        # 6. CÀLCUL DE MÀXIMES, MÍNIMES I PLUJA ACUMULADA (Ítems 3, 4)
        valors_tx = [f['tx'] for f in files_dades if f.get('tx') is not None]
        valors_tn = [f['tn'] for f in files_dades if f.get('tn') is not None]
        valors_pluja = [f['pluja'] for f in files_dades if f.get('pluja') is not None]
        
        # 7. GENERAR I GUARDAR EL FITXER DE TREBALL (JSON)
        data_avui = datetime.now().strftime('%Y-%m-%d')
        nom_fitxer_cache = f"{cache_file_prefix}_{codi_estacio}_{data_avui}.json"
        
        dades_diaries = {
            'estacio': codi_estacio,
            'data_processament': datetime.now().isoformat(),
            'dades_periodiques': files_dades,
            'calculs': {
                'temperatura_maxima': max(valors_tx) if valors_tx else None,
                'temperatura_minima': min(valors_tn) if valors_tn else None,
                'pluja_acumulada': sum(valors_pluja) if valors_pluja else 0.0,
                'periode_referencia': dades_actuals.get('periode')
            }
        }
        
        with open(nom_fitxer_cache, 'w', encoding='utf-8') as f:
            json.dump(dades_diaries, f, indent=2, ensure_ascii=False)
        
        # 8. PREPARAR EL RESULTAT FINAL PER AL TICKER
        resultat = {
            'estacio': codi_estacio,
            'url_font': url,
            'actual': {
                'periode': dades_actuals.get('periode'),
                'temperatura': dades_actuals.get('tm_actual'),
                'humitat': dades_actuals.get('humitat'),
                'vent_vel_mitjana': dades_actuals.get('vent_vel_mitjana'),
                'vent_dir_mitjana': dades_actuals.get('vent_dir_mitjana'),
                'pressio': dades_actuals.get('pressio'),
                'radiacio': dades_actuals.get('radiacio')
            },
            'resum_dia': {
                'temperatura_maxima': dades_diaries['calculs']['temperatura_maxima'],
                'temperatura_minima': dades_diaries['calculs']['temperatura_minima'],
                'pluja_acumulada': dades_diaries['calculs']['pluja_acumulada']
            },
            'fitxer_cache': nom_fitxer_cache
        }
        
        print(f"[OK] Dades processades per a {codi_estacio}. Cache: {nom_fitxer_cache}")
        return resultat
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Fallada de xarxa per a {codi_estacio}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Processant {codi_estacio}: {e}", file=sys.stderr)
    
    return None

def renderitzar_html(dades_XJ: Dict, dades_UO: Dict) -> str:
    """
    Genera el codi HTML final del ticker a partir de les dades.
    Aquest és el teu disseny actual.
    """
    # Funció auxiliar per formatar valors (afegeix unitats si cal)
    def fmt(val, unitat=''):
        if val is None:
            return 'N/D'
        if isinstance(val, float):
            if val.is_integer():
                val = int(val)
            return f'{val}{unitat}'
        return str(val)
    
    hora_actual = datetime.now().strftime('%H:%M')
    data_actual = datetime.now().strftime('%d/%m/%Y')
    
    html = f'''<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticker Meteorològic</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* (EL TEU ESTIL ACTUAL - NO EL MODIFIQUEM) */
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
        /* Colors per a icones (segons el teu disseny) */
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
        <!-- ESTACIÓ GIRONA (XJ) -->
        <div class="estacio">
            <div class="header">
                <i class="fas fa-map-marker-alt"></i>
                <h3>GIRONA</h3>
            </div>
            <div class="temps-actual">Període: {dades_XJ.get('actual', {}).get('periode', 'N/D')}</div>
            <div class="dades">
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-temperature-high"></i> Actual</div>
                    <div class="valor">{fmt(dades_XJ.get('actual', {}).get('temperatura'), '°')}<span class="unitat">C</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-temperature-high"></i> Màx</div>
                    <div class="valor">{fmt(dades_XJ.get('resum_dia', {}).get('temperatura_maxima'), '°')}<span class="unitat">C</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-temperature-low"></i> Mín</div>
                    <div class="valor">{fmt(dades_XJ.get('resum_dia', {}).get('temperatura_minima'), '°')}<span class="unitat">C</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-tint"></i> Humitat</div>
                    <div class="valor">{fmt(dades_XJ.get('actual', {}).get('humitat'), '')}<span class="unitat">%</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-cloud-rain"></i> Pluja</div>
                    <div class="valor">{fmt(dades_XJ.get('resum_dia', {}).get('pluja_acumulada'), '')}<span class="unitat">mm</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-wind"></i> Vent</div>
                    <div class="valor">{fmt(dades_XJ.get('actual', {}).get('vent_vel_mitjana'), '')}<span class="unitat">km/h</span></div>
                </div>
            </div>
        </div>

        <!-- ESTACIÓ FORNELLS DE LA SELVA (UO) -->
        <div class="estacio">
            <div class="header">
                <i class="fas fa-map-marker-alt"></i>
                <h3>FORNELLS DE LA SELVA</h3>
            </div>
            <div class="temps-actual">Període: {dades_UO.get('actual', {}).get('periode', 'N/D')}</div>
            <div class="dades">
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-temperature-high"></i> Actual</div>
                    <div class="valor">{fmt(dades_UO.get('actual', {}).get('temperatura'), '°')}<span class="unitat">C</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-temperature-high"></i> Màx</div>
                    <div class="valor">{fmt(dades_UO.get('resum_dia', {}).get('temperatura_maxima'), '°')}<span class="unitat">C</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-temperature-low"></i> Mín</div>
                    <div class="valor">{fmt(dades_UO.get('resum_dia', {}).get('temperatura_minima'), '°')}<span class="unitat">C</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-tint"></i> Humitat</div>
                    <div class="valor">{fmt(dades_UO.get('actual', {}).get('humitat'), '')}<span class="unitat">%</span></div>
                </div>
                <div class="dada">
                    <div class="etiqueta"><i class="fas fa-cloud-rain"></i> Pluja</div>
                    <div class="valor">{fmt(dades_UO.get('resum_dia', {}).get('pluja_acumulada'), '')}<span class="unitat">mm</span></div>
                </div>
                <div class="dada">
                    <!-- Nota: Fornells no té dades de vent a la taula, per això es mostra N/D -->
                    <div class="etiqueta"><i class="fas fa-wind"></i> Vent</div>
                    <div class="valor">{fmt(dades_UO.get('actual', {}).get('vent_vel_mitjana'), '')}<span class="unitat">km/h</span></div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="timestamp">
        <i class="far fa-clock"></i> Dades actualitzades a les {hora_actual} del {data_actual} |
        Font: <a href="https://meteo.cat" style="color:#4dabf7;">Servei Meteorològic de Catalunya</a>
    </div>
</body>
</html>
'''
    return html

# ============================================================================
# EXECUCIÓ PRINCIPAL
# ============================================================================

def main():
    """Funció principal del script."""
    print("=" * 60)
    print("INICIANT GENERACIÓ DEL TICKER METEOROLÒGIC")
    print("=" * 60)
    
    # 1. OBTENIR DADES DE LES DUES ESTACIONS
    print("\n[1] Obtenint dades de Meteo.cat...")
    dades_XJ = obtenir_dades_estacio('XJ', cache_file_prefix="meteo_cache")
    dades_UO = obtenir_dades_estacio('UO', cache_file_prefix="meteo_cache")
    
    # 2. COMPROVAR SI TENIM DADES SUFICENTS
    if not dades_XJ or not dades_UO:
        print("[ERROR] No s'han pogut obtenir dades completes. Surtint.", file=sys.stderr)
        sys.exit(1)
    
    # 3. GENERAR L'HTML
    print("\n[2] Generant HTML...")
    html_final = renderitzar_html(dades_XJ, dades_UO)
    
    # 4. ESCRIURE EL FITXER INDEX.HTML
    output_file = Path("index.html")
    output_file.write_text(html_final, encoding='utf-8')
    
    print(f"[OK] HTML generat correctament a: {output_file.resolve()}")
    print(f"\n✅ PROCÉS COMPLETAT. Ticker actualitzat.")
    print("=" * 60)

if __name__ == "__main__":
    main()
