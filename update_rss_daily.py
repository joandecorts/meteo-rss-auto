import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import Dict, Any, Optional

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
        # ===============================
        # Busquem la taula que conté les dades periòdiques.
        # S'identifica per l'encapçalament 'PeríodeTU'. Això és més robust que un id específic.
        taula = None
        for table in soup.find_all('table'):
            if table.find('th', string='PeríodeTU'):
                taula = table
                break
        
        if not taula:
            print(f"[ERROR] No s'ha trobat la taula de dades per a {codi_estacio}")
            return None
        
        # 2. MAPEJAR ELS TÍTOLS DE LES COLUMNES
        # ======================================
        # Agafem la primera fila (<tr>) de la taula, que conté els <th> amb els noms.
        fila_capsalera = taula.find('tr')
        capsaleres = [th.get_text(strip=True) for th in fila_capsalera.find_all(['th', 'td'])]
        
        # Creem un diccionari per trobar ràpidament l'índex d'una columna pel seu nom.
        # Exemple: {'PeríodeTU': 0, 'TX°C': 2, 'PPTmm': 5, ...}
        index_columna = {nom: idx for idx, nom in enumerate(capsaleres)}
        
        # 3. DEFINIR LES COLUMNES QUE ENS INTERESSEN I LES SEVES CLAUS
        # ============================================================
        # Cada element és una tupla: (nom_columna_html, clau_diccionari_sortida, tipus_dada)
        columnes_a_extreure = [
            ('PeríodeTU', 'periode', 'text'),
            ('TM°C', 'tm_actual', 'float'),   # Temperatura actual
            ('TX°C', 'tx', 'float'),          # Per a càlcul de MÀXIMA
            ('TN°C', 'tn', 'float'),          # Per a càlcul de MÍNIMA
            ('HRM%', 'humitat', 'float'),
            ('PPTmm', 'pluja', 'float'),      # Per a càlcul d'ACUMULADA
            ('VVM (10 m)km/h', 'vent_vel_mitjana', 'float'),
            ('DVM (10 m)graus', 'vent_dir_mitjana', 'float'),
            ('VVX (10 m)km/h', 'vent_vel_maxima', 'float'),
            ('PMhPa', 'pressio', 'float'),
            ('RSW/m2', 'radiacio', 'float')
        ]
        
        # 4. RECOLLIR TOTES LES FILES DE DADES DEL DIA
        # ============================================
        # Això resol els teus punts 5 i 6: llegim TOTS els períodes.
        files_dades = []
        for fila in taula.find_all('tr')[1:]:  # Saltem la fila de la capçalera
            cel·les = fila.find_all(['td', 'th'])
            if len(cel·les) != len(capsaleres):
                continue  # Ens saltem files incompletes
            
            fila_dict = {'_raw_cells': [c.get_text(strip=True) for c in cel·les]}
            
            # Per a cada columna que volem, mirem si existeix i processem el valor.
            for nom_col_html, clau, tipus in columnes_a_extreure:
                if nom_col_html in index_columna:
                    idx = index_columna[nom_col_html]
                    valor_text = cel·les[idx].get_text(strip=True)
                    
                    # Gestió de valors especials com '(s/d)' o buits.
                    if valor_text in ('(s/d)', '', '-', 'N/D'):
                        valor = None
                    else:
                        try:
                            if tipus == 'float':
                                valor = float(valor_text)
                            else:
                                valor = valor_text
                        except ValueError:
                            valor = valor_text  # Si no es pot convertir, es guarda com a text
                    fila_dict[clau] = valor
                else:
                    # Si la columna no existeix en aquesta taula, posem None.
                    # AQUEST ÉS EL COR DEL BLINDATGE PER A FORNELLS (UO).
                    fila_dict[clau] = None
            
            # Només afegim la fila si el període no és buit.
            if fila_dict.get('periode'):
                files_dades.append(fila_dict)
        
        if not files_dades:
            print(f"[ERROR] No s'han trobat dades vàlides per a {codi_estacio}")
            return None
        
        # 5. OBTENCIÓ DE L'ÚLTIM PERÍODE VÀLID (Ítems 1, 2)
        # ==================================================
        # Cerquem des del final cap al principi la primera fila amb dades de temperatura.
        dades_actuals = None
        for fila in reversed(files_dades):
            if fila.get('tm_actual') is not None:
                dades_actuals = fila
                break
        
        if not dades_actuals:
            dades_actuals = files_dades[-1]  # Fallback: l'última fila
        
        # 6. CÀLCUL DE MÀXIMES, MÍNIMES I PLUJA ACUMULADA (Ítems 3, 4)
        # ============================================================
        # Preparem les llistes de valors, ignorant els None.
        valors_tx = [f['tx'] for f in files_dades if f.get('tx') is not None]
        valors_tn = [f['tn'] for f in files_dades if f.get('tn') is not None]
        valors_pluja = [f['pluja'] for f in files_dades if f.get('pluja') is not None]
        
        # 7. GENERAR I GUARDAR EL FITXER DE TREBALL (JSON) - Part de l'ítem 6
        # ===================================================================
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
        
        # Guardem el JSON (podries desar aquest fitxer per a anàlisis o debug).
        with open(nom_fitxer_cache, 'w', encoding='utf-8') as f:
            json.dump(dades_diaries, f, indent=2, ensure_ascii=False)
        
        # 8. PREPARAR EL RESULTAT FINAL PER AL TICKER
        # ===========================================
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
        print(f"[ERROR] Fallada de xarxa per a {codi_estacio}: {e}")
    except Exception as e:
        print(f"[ERROR] Processant {codi_estacio}: {e}")
    
    return None

# -----------------------------------------------------------
# EXEMPLE D'ÚS DINS DEL TEU generate_meteo_rss.py
# -----------------------------------------------------------
if __name__ == "__main__":
    # Obtenir dades per a les dues estacions
    dades_XJ = obtenir_dades_estacio('XJ', cache_file_prefix="meteo_cache")
    dades_UO = obtenir_dades_estacio('UO', cache_file_prefix="meteo_cache")
    
    # Aquí integraries aquestes dades al teu template HTML...
    # Per exemple:
    # template_data = {
    #     'girona': dades_XJ,
    #     'fornells': dades_UO,
    #     'data_actualitzacio': datetime.now().strftime('%H:%M')
    # }
    # ... renderitzar template i generar HTML ...
