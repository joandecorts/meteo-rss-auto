def obtenir_dades_del_rss(url_rss: str = 'https://joandecorts.github.io/meteo-rss-auto/meteo.rss') -> List[Dict[str, Any]]:
    """
    Llegeix el fitxer RSS i extreu les dades de totes les estacions.
    FILTRA només les estacions de Girona i Fornells de la Selva.
    """
    try:
        print(f"[INFO] Obtenint dades del RSS: {url_rss}")
        
        with urllib.request.urlopen(url_rss) as response:
            rss_content = response.read().decode('utf-8')
        
        print("[OK] RSS obtingut correctament")
        
        # Trobar TOTS els items del RSS
        items = re.findall(r'<item>(.*?)</item>', rss_content, re.DOTALL)
        print(f"[INFO] Trobats {len(items)} items totals al RSS")
        
        stations_data = []
        estacions_demanades = ['Girona', 'Fornells de la Selva']
        estacions_trobades = []
        
        for i, item in enumerate(items):
            # Extreure el títol de l'ítem
            title_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
            
            if not title_match:
                continue
            
            title_text = title_match.group(1).strip()
            
            # DETECTAR SI AQUEST ÉS UN ITEM VÀLID D'ESTACIÓ METEOROLÒGICA
            # Busquem patrons que indiquin que és una estació meteorològica
            es_estacio_meteo = False
            nom_estacio = None
            
            # Patró 1: Conté l'emoji de núvol i temperatura 🌤️
            if '🌤️' in title_text:
                es_estacio_meteo = True
                # Extreure nom entre 🌤️ i |
                name_match = re.search(r'🌤️\s*(.*?)\s*\|', title_text)
                if name_match:
                    nom_estacio = name_match.group(1).strip()
            
            # Patró 2: Conté paraules clau meteorològiques
            elif any(keyword in title_text for keyword in ['Temp.', 'Humitat:', 'Vent:', 'Precipitació:']):
                es_estacio_meteo = True
                # Intentar extreure nom del títol
                nom_estacio = "Estació Meteorològica"
            
            # Si no és una estació meteorològica, saltem aquest ítem
            if not es_estacio_meteo:
                continue
            
            # FILTRAR: Només processem Girona i Fornells de la Selva
            if nom_estacio and any(estacio_demanada in nom_estacio for estacio_demanada in estacions_demanades):
                estacions_trobades.append(nom_estacio)
                
                # Inicialitzar dades de l'estació
                station_data = {
                    'name': nom_estacio,
                    'code': "",
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
                
                # Determinar codi de l'estació pel nom
                if 'Girona' in nom_estacio:
                    station_data['code'] = 'XJ'
                elif 'Fornells' in nom_estacio:
                    station_data['code'] = 'UO'
                
                # EXTREURE LES DADES METEOROLÒGIQUES (mateix codi que abans)
                # Temperatura Actual
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
                
                stations_data.append(station_data)
                print(f"[OK] Processada estació vàlida: {nom_estacio}")
        
        print(f"[OK] Estacions filtrades: {', '.join(estacions_trobades)}")
        print(f"[OK] Total estacions vàlides: {len(stations_data)}")
        
        # Si no hem trobat cap estació vàlida, provem una estratègia més agressiva
        if len(stations_data) == 0:
            print("[WARNING] No s'han trobat estacions amb els filtres. Processant totes...")
            # Aquí podries afegir codi de backup per processar tots els ítems
        
        return stations_data
        
    except Exception as e:
        print(f"[ERROR] Obtenint dades del RSS: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []
