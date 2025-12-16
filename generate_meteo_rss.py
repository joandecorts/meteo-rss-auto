#!/usr/bin/env python3
"""
Script principal per generar l'HTML del ticker meteorològic.
Actualitza les dades de Girona (XJ) i Fornells de la Selva (UO).
Funciona amb l'estructura HTML de www.meteo.cat.
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# ============================================================================
# FUNCIÓ PRINCIPAL D'OBTENCIÓ DE DADES (VERSIÓ DEFINITIVA)
# ============================================================================

def obtenir_dades_estacio(codi_estacio: str, cache_file_prefix: str = "meteo_cache") -> Optional[Dict[str, Any]]:
    """
    Obté i processa les dades d'una estació XEMA de Meteo.cat.
    Cerca la taula per l'id 'tblperiode' i processa totes les files del dia.
    """
    base_url = "https://www.meteo.cat/observacions/xema/dades"
    url = f"{base_url}?codi={codi_estacio}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. LOCALITZAR LA TAULA PER ID (COM AL TEU XAT ANTERIOR)
        # =====================================================
        taula = soup.find('table', {'id': 'tblperiode'})
        
        if not taula:
            # Si per algun motiu no troba l'id, prova amb una cerca de seguretat
            print(f"[INFO] No s'ha trobat 'tblperiode' per a {codi_estacio}. Cercant per encapçalament...")
            for table in soup.find_all('table'):
                if table.find('th', string=lambda t: t and 'Període' in t):
                    taula = table
                    break
        
        if not taula:
            print(f"[ERROR] No s'ha trobat la taula de dades per a {codi_estacio}", file=sys.stderr)
            return None
        
        # 2. EXTREURE CAPÇALERES PER MAPEJAR COLUMNES
        # ============================================
        fila_capsalera = taula.find('tr')
        if not fila_capsalera:
            print(f"[ERROR] La taula no té capçalera per a {codi_estacio}", file=sys.stderr)
            return None
        
        # Obtenir tots els textos dels encapçalaments (th o td de la primera fila)
        capsaleres = []
        for cell in fila_capsalera.find_all(['th', 'td']):
            text = cell.get_text(strip=True)
            # Netejar el text: alguns poden tenir espais o salts de línia
            capsaleres.append(text)
        
        # Crear un diccionari per trobar l'índex d'una columna pel seu nom
        # Exemple: {'Període': 0, 'TM°C': 1, 'TX°C': 2, ...}
        index_columna = {}
        for idx, nom in enumerate(capsaleres):
            # Si hi ha múltiples columnes amb el mateix nom (poc probable),
            # només guardem el primer índex
            if nom not in index_columna:
                index_columna[nom] = idx
        
        # 3. DEFINIR QUINES COLUMNES ENS INTERESSEN
        # =========================================
        # Aquestes són les columnes que podrien aparèixer a la taula
        # Afegim múltiples possibles noms per a la mateixa dada per ser flexibles
        columnes_a_buscar = {
            'periode': ['Període', 'PeríodeTU'],
            'tm_actual': ['TM', 'TM°C', 'Temperatura mitjana'],
            'tx': ['TX', 'TX°C', 'Temperatura màxima'],
            'tn': ['TN', 'TN°C', 'Temperatura mínima'],
            'humitat': ['HRM', 'HRM%', 'Humitat relativa mitjana'],
            'pluja': ['PPT', 'PPTmm', 'Precipitació'],
            'vent_vel_mitjana': ['VVM', 'VVM (10 m)km/h', 'Vent mitjà'],
            'vent_dir_mitjana': ['DVM', 'DVM (10 m)graus', 'Direcció vent mitjà'],
            'vent_vel_maxima': ['VVX', 'VVX (10 m)km/h', 'Ratxa màxima'],
            'pressio': ['PM', 'PMhPa', 'Pressió'],
            'radiacio': ['RS', 'RSW/m2', 'Radiació']
        }
        
        # 4. RECOLLIR TOTES LES FILES DE DADES DEL DIA
        # ============================================
        files_dades = []
        files_taula = taula.find_all('tr')[1:]  # Saltem la primera fila (capçalera)
        
        for fila in files_taula:
            cel·les = fila.find_all(['td', 'th'])
            
            # Només processem files amb el nombre correcte de cel·les
            if len(cel·les) < 3:  # Com a mínim ha de tenir Període, TM i una altra dada
                continue
            
            fila_dict = {}
            
            # Per a cada tipus de dada que volem, busquem la columna corresponent
            for clau, possibles_noms in columnes_a_buscar.items():
                valor = None
                
                # Busquem quina columna coincideix amb els noms possibles
                for nom_possible in possibles_noms:
                    if nom_possible in index_columna:
                        idx = index_columna[nom_possible]
                        if idx < len(cel·les):
                            text_valor = cel·les[idx].get_text(strip=True)
                            
                            # Tractar valors especials
                            if text_valor and text_valor not in ('(s/d)', '-', 'N/D', ''):
                                try:
                                    # Intentar convertir a float si sembla un número
                                    if '°' in nom_possible or '%' in nom_possible or 'mm' in nom_possible or 'km/h' in nom_possible or 'hPa' in nom_possible:
                                        valor = float(text_valor)
                                    else:
                                        valor = text_valor
                                except ValueError:
                                    valor = text_valor
                        break  # Sortim del bucle de noms possibles si trobem una coincidència
                
                fila_dict[clau] = valor
            
            # Només afegim la fila si té un període definit
            if fila_dict.get('periode'):
                files_dades.append(fila_dict)
        
        if not files_dades:
            print(f"[ERROR] No s'han trobat dades vàlides per a {codi_estacio}", file=sys.stderr)
            return None
        
        # 5. OBTENCIÓ DE L'ÚLTIM PERÍODE VÀLID (Ítems 1 i 2)
        # ====================================================
        dades_actuals = None
        for fila in reversed(files_dades):
            if fila.get('tm_actual') is not None:
                dades_actuals = fila
                break
        
        # Fallback: si no trobem dades vàlides, agafem l'última fila
        if not dades_actuals:
            dades_actuals = files_dades[-1]
        
        # 6. CÀLCUL DE MÀXIMES, MÍNIMES I PLUJA ACUMULADA (Ítems 3 i 4)
        # =============================================================
        # Agafem valors vàlids (no None) de totes les files
        valors_tx = [f['tx'] for f in files_dades if f.get('tx') is not None]
        valors_tn = [f['tn'] for f in files_dades if f.get('tn') is not None]
        valors_pluja = [f['pluja'] for f in files_dades if f.get('pluja') is not None]
        
        temperatura_maxima = max(valors_tx) if valors_tx else None
        temperatura_minima = min(valors_tn) if valors_tn else None
        pluja_acumulada = sum(valors_pluja) if valors_pluja else 0.0
        
        # 7. GENERAR EL FITXER DE TREBALL JSON (Ítem 6)
        # ============================================
        data_avui = datetime.now().strftime('%Y-%m-%d')
        nom_fitxer_cache = f"{cache_file_prefix}_{codi_estacio}_{data_avui}.json"
        
        dades_diaries = {
            'estacio': codi_estacio,
            'data_processament': datetime.now().isoformat(),
            'url_font': url,
            'dades_periodiques': files_dades,
            'calculs': {
                'temperatura_maxima': temperatura_maxima,
                'temperatura_minima': temperatura_minima,
                'pluja_acumulada': pluja_acumulada,
                'periode_referencia': dades_actuals.get('periode'),
                'total_periodes': len(files_dades)
            }
        }
        
        with open(nom_fitxer_cache, 'w', encoding='utf-8') as f:
            json.dump(dades_diaries, f, indent=2, ensure_ascii=False)
        
        # 8. PREPARAR EL RESULTAT PER AL TICKER HTML
        # ==========================================
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
                'temperatura_maxima': temperatura_maxima,
                'temperatura_minima': temperatura_minima,
                'pluja_acumulada': pluja_acumulada
            },
            'fitxer_cache': nom_fitxer_cache,
            'total_periodes': len(files_dades)
        }
        
        print(f"[OK] Dades processades per a {codi_estacio} ({len(files_dades)} períodes)")
        return resultat
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Fallada de xarxa per a {codi_estacio}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Processant {codi_estacio}: {e}", file=sys.stderr)
    
    return None

# ============================================================================
# GENERACIÓ DE L'HTML (EL TEU DISSENY)
# ============================================================================

def renderitzar_html(dades_XJ: Dict, dades_UO: Dict) -> str:
    """Genera el codi HTML del ticker."""
    
    def fmt(val, unitat=''):
        """Formata un valor per a mostrar-lo."""
        if val is None:
            return 'N/D'
        if isinstance(val, float):
            # Sense colors als dígits (només text blanc)
            if val.is_integer():
                return f'{int(val)}{unitat}'
            # Mostra un decimal, neteja zeros innecessaris
            return f'{val:.1f}{unitat}'.rstrip('0').rstrip('.') + unitat
        return str(val)
    
    hora_actual = datetime.now().strftime('%H:%M')
    data_actual = datetime.now().strftime('%d/%m/%Y')
    
    # TEMPLATE HTML
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
        <!-- GIRONA -->
        <div class="estacio">
            <div class="header">
                <i class="fas fa-map-marker-alt"></i>
                <h3>GIRONA</h3>
            </div>
            <div class="temps-actual">Període: {dades_XJ.get('actual', {}).get('periode', 'N/D')}</div>
            <div class="dades">
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Actual</div><div class="valor">{fmt(dades_XJ.get('actual', {}).get('temperatura'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Màx</div><div class="valor">{fmt(dades_XJ.get('resum_dia', {}).get('temperatura_maxima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-low"></i> Mín</div><div class="valor">{fmt(dades_XJ.get('resum_dia', {}).get('temperatura_minima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-tint"></i> Humitat</div><div class="valor">{fmt(dades_XJ.get('actual', {}).get('humitat'), '')}<span class="unitat">%</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-cloud-rain"></i> Pluja</div><div class="valor">{fmt(dades_XJ.get('resum_dia', {}).get('pluja_acumulada'), '')}<span class="unitat">mm</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-wind"></i> Vent</div><div class="valor">{fmt(dades_XJ.get('actual', {}).get('vent_vel_mitjana'), '')}<span class="unitat">km/h</span></div></div>
            </div>
        </div>
        
        <!-- FORNELLS -->
        <div class="estacio">
            <div class="header">
                <i class="fas fa-map-marker-alt"></i>
                <h3>FORNELLS DE LA SELVA</h3>
            </div>
            <div class="temps-actual">Període: {dades_UO.get('actual', {}).get('periode', 'N/D')}</div>
            <div class="dades">
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Actual</div><div class="valor">{fmt(dades_UO.get('actual', {}).get('temperatura'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-high"></i> Màx</div><div class="valor">{fmt(dades_UO.get('resum_dia', {}).get('temperatura_maxima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-temperature-low"></i> Mín</div><div class="valor">{fmt(dades_UO.get('resum_dia', {}).get('temperatura_minima'), '°')}<span class="unitat">C</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-tint"></i> Humitat</div><div class="valor">{fmt(dades_UO.get('actual', {}).get('humitat'), '')}<span class="unitat">%</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-cloud-rain"></i> Pluja</div><div class="valor">{fmt(dades_UO.get('resum_dia', {}).get('pluja_acumulada', 0), '')}<span class="unitat">mm</span></div></div>
                <div class="dada"><div class="etiqueta"><i class="fas fa-wind"></i> Vent</div><div class="valor">{fmt(dades_UO.get('actual', {}).get('vent_vel_mitjana'), '')}<span class="unitat">km/h</span></div></div>
            </div>
        </div>
    </div>
    
    <div class="timestamp">
        <i class="far fa-clock"></i> Dades actualitzades a les {hora_actual} del {data_actual} |
        Font: <a href="https://meteo.cat" style="color:#4dabf7;">Servei Meteorològic de Catalunya</a>
    </div>
</body>
</html>'''
    return html

# ============================================================================
# EXECUCIÓ PRINCIPAL
# ============================================================================

def main():
    print("=" * 60)
    print("INICIANT GENERACIÓ DEL TICKER METEOROLÒGIC")
    print("=" * 60)
    
    # 1. OBTENIR DADES
    print("\n[1] Obtenint dades de Meteo.cat...")
    dades_XJ = obtenir_dades_estacio('XJ')
    dades_UO = obtenir_dades_estacio('UO')
    
    if not dades_XJ or not dades_UO:
        print("[ERROR] No s'han pogut obtenir dades completes. Surtint.", file=sys.stderr)
        sys.exit(1)
    
    # 2. GENERAR HTML
    print("[2] Generant HTML...")
    html_final = renderitzar_html(dades_XJ, dades_UO)
    
    # 3. ESCRIURE FITXER
    output_file = Path("index.html")
    output_file.write_text(html_final, encoding='utf-8')
    
    print(f"[OK] HTML generat: {output_file.resolve()}")
    print(f"[OK] Fitxers JSON creats: {dades_XJ.get('fitxer_cache')}, {dades_UO.get('fitxer_cache')}")
    print("\n✅ TICKER ACTUALITZAT CORRECTAMENT")
    print("=" * 60)

if __name__ == "__main__":
    main()
