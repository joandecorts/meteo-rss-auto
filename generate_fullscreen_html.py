#!/usr/bin/env python3
# generate_fullscreen_html.py - VERSIÓ FINAL DEFINITIVA CORREGIDA
# CORRECCIONS: 
# 1. Elimina JavaScript que canvia l'hora cada minut
# 2. Canvia "Meteo.cat" per "Font: https://www.meteo.cat/"
# 3. Hora d'actualització en CAT (no UTC)

import json
from datetime import datetime
import os
import pytz  # <-- NOU IMPORT

def convert_utc_to_cat(utc_time_str):
    """Converteix hora UTC a hora local CAT"""
    try:
        if not utc_time_str or utc_time_str == 'N/D':
            return utc_time_str
            
        # Parseja l'hora UTC
        utc_time = datetime.strptime(utc_time_str, "%H:%M")
        
        # Assumim que és avui
        today = datetime.now().date()
        utc_datetime = datetime.combine(today, utc_time.time())
        
        # Aplica zona horària
        utc_zone = pytz.utc
        cat_zone = pytz.timezone('Europe/Madrid')
        
        # Converteix
        utc_datetime = utc_zone.localize(utc_datetime)
        cat_datetime = utc_datetime.astimezone(cat_zone)
        
        # Formata com a hora local
        return cat_datetime.strftime("%H:%M") + " (CAT)"
        
    except Exception as e:
        print(f"⚠️  Error convertint hora {utc_time_str}: {e}")
        return utc_time_str

def read_weather_summary():
    """Llegeix el fitxer de resum de dades"""
    try:
        with open('data/weather_summary.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error llegint weather_summary.json: {e}")
        return None

def format_temperature(temp):
    """Formata temperatura amb un decimal"""
    if temp is None:
        return "N/D"
    return f"{temp:.1f}"

def format_rain(rain):
    """Formata pluja amb un decimal"""
    if rain is None:
        return "0.0"
    return f"{rain:.1f}"

def create_html_for_station(station_data, station_code, station_name):
    """Crea HTML final amb els darrers ajustos"""
    
    # Hora de l'actualització (la que està al JSON)
    update_time = station_data.get('updated_at', 'N/D')
    
    # Crear contingut HTML
    html_content = f'''<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Weather - {station_name}</title>
    <style>
        /* RESET TOTAL */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        
        body {{
            background: linear-gradient(135deg, #2196F3 0%, #0D47A1 100%);
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 10px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
        }}
        
        /* CONTENIDOR PRINCIPAL */
        .container {{
            width: 95%;
            max-width: 1400px;
            height: auto;
            min-height: 85vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 15px;
            gap: 15px;
        }}
        
        /* BANNER ESTACIÓ - FONS NEGRE */
        .station-banner {{
            background: rgba(0, 0, 0, 0.85);
            color: #4CAF50;
            font-size: clamp(40px, 6vw, 70px);
            font-weight: 800;
            padding: 12px 30px;
            border-radius: 15px;
            border: 3px solid #4CAF50;
            width: 90%;
            max-width: 1000px;
            margin-bottom: 5px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* INFO DATA I HORA */
        .header-info {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            margin-bottom: 10px;
            width: 90%;
        }}
        
        .info-box {{
            background: rgba(255, 255, 255, 0.15);
            padding: 10px 20px;
            border-radius: 10px;
            border: 2px solid rgba(255, 255, 255, 0.25);
            font-size: clamp(18px, 2.5vw, 28px);
            font-weight: 600;
            min-width: 250px;
        }}
        
        /* PERÍODE */
        .period-box {{
            background: rgba(0, 0, 0, 0.6);
            padding: 8px 20px;
            border-radius: 10px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            margin: 5px 0;
            width: 85%;
            max-width: 800px;
        }}
        
        .period-main {{
            font-size: clamp(16px, 2.2vw, 24px);
            color: #FFFFFF;
            font-weight: 600;
        }}
        
        .period-note {{
            font-size: clamp(12px, 1.5vw, 16px);
            color: #BBDAFF;
            opacity: 0.8;
            font-style: italic;
            margin-top: 3px;
        }}
        
        .period-asterisk {{
            color: #FFCC80; /* GROC */
            font-weight: bold;
            margin-left: 2px;
        }}
        
        /* DADES PRINCIPALS */
        .data-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            width: 95%;
            max-width: 1300px;
            margin: 10px 0;
        }}
        
        .data-box {{
            background: rgba(255, 255, 255, 0.18);
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 15px;
            padding: 20px 25px;
            flex: 1;
            min-width: 250px;
            max-width: 350px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }}
        
        .data-box:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        }}
        
        .data-label {{
            font-size: clamp(16px, 2vw, 22px);
            color: #FFFFFF;
            font-weight: 600;
            margin-bottom: 10px;
            min-height: 50px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        .data-value {{
            font-size: clamp(40px, 5.5vw, 65px);
            font-weight: 800;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            line-height: 1;
        }}
        
        .temperature-max .data-value {{
            color: #FF5252;
        }}
        
        .temperature-min .data-value {{
            color: #29B6F6;
        }}
        
        .rain-total .data-value {{
            color: #80DEEA;
        }}
        
        .data-unit {{
            font-size: clamp(20px, 3vw, 30px);
            opacity: 0.9;
            margin-left: 4px;
            color: #E3F2FD;
        }}
        
        .temperature-icon {{
            font-size: clamp(22px, 3vw, 30px);
            margin-bottom: 8px;
        }}
        
        /* PEU DE PÀGINA - CORREGIT */
        .footer {{
            font-size: clamp(12px, 1.5vw, 18px);
            color: #A3D5FF;
            opacity: 0.7;
            margin-top: 15px;
            text-align: center;
            width: 100%;
        }}
        
        /* ASTERISC GROC A LA NOTA TAMBÉ */
        .note-asterisk {{
            color: #FFCC80; /* GROC IGUAL QUE A DALT */
            font-weight: bold;
            margin-left: 2px;
        }}
        
        /* RESPONSIVE */
        @media (max-width: 1024px) {{
            .container {{
                padding: 10px;
                gap: 10px;
            }}
            
            .data-box {{
                min-width: 220px;
                padding: 15px 20px;
            }}
            
            .header-info {{
                gap: 10px;
            }}
            
            .info-box {{
                min-width: 200px;
                padding: 8px 15px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .station-banner {{
                font-size: clamp(30px, 8vw, 50px);
                padding: 10px 20px;
            }}
            
            .data-container {{
                flex-direction: column;
                align-items: center;
            }}
            
            .data-box {{
                width: 90%;
                max-width: 400px;
            }}
        }}
        
        @media (max-width: 480px) {{
            body {{
                padding: 5px;
            }}
            
            .container {{
                padding: 8px;
                gap: 8px;
            }}
            
            .station-banner {{
                padding: 8px 15px;
                font-size: clamp(25px, 7vw, 40px);
            }}
            
            .data-box {{
                padding: 12px 15px;
                width: 95%;
            }}
            
            .info-box {{
                min-width: 90%;
            }}
        }}
        
        /* ANIMACIONS */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.8s ease-out;
            opacity: 0;
            animation-fill-mode: forwards;
        }}
        
        .delay-1 {{ animation-delay: 0.1s; }}
        .delay-2 {{ animation-delay: 0.2s; }}
        .delay-3 {{ animation-delay: 0.3s; }}
        .delay-4 {{ animation-delay: 0.4s; }}
        .delay-5 {{ animation-delay: 0.5s; }}
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌤️</text></svg>">
</head>
<body>
    <div class="container">
        <!-- BANNER NEGRE AMB NOM -->
        <div class="station-banner fade-in">
            <i class="fas fa-map-marker-alt"></i> {station_name}
        </div>
        
        <!-- INFO SUPERIOR - HORA FIXA (NO canvia) -->
        <div class="header-info fade-in delay-1">
            <div class="info-box">
                <i class="far fa-calendar-alt"></i> {station_data.get('date_spanish', 'N/D')}
            </div>
            <div class="info-box">
                <i class="fas fa-sync-alt"></i> {convert_utc_to_cat(update_time)}
            </div>
        </div>
        
        <!-- PERÍODE -->
        <div class="period-box fade-in delay-2">
            <div class="period-main">
                <i class="fas fa-clock"></i> {station_data.get('last_period_utc', station_data.get('last_period', 'N/D'))} UTC<span class="period-asterisk">*</span>
            </div>
            <div class="period-note">
                <span class="note-asterisk">*</span> Sumar 1 hora (hivern) o 2 hores (estiu) per a l'hora local
            </div>
        </div>
        
        <!-- DADES PRINCIPALS - AMB TEXT COMPLET -->
        <div class="data-container">
            <div class="data-box temperature-max fade-in delay-3">
                <div class="data-label">
                    <i class="fas fa-thermometer-full temperature-icon"></i>
                    Màxima del dia
                </div>
                <div class="data-value">
                    {format_temperature(station_data.get('max_temp'))}<span class="data-unit">ºC</span>
                </div>
            </div>
            
            <div class="data-box temperature-min fade-in delay-4">
                <div class="data-label">
                    <i class="fas fa-thermometer-empty temperature-icon"></i>
                    Mínima del dia
                </div>
                <div class="data-value">
                    {format_temperature(station_data.get('min_temp'))}<span class="data-unit">ºC</span>
                </div>
            </div>
            
            <div class="data-box rain-total fade-in delay-5">
                <div class="data-label">
                    <i class="fas fa-cloud-rain temperature-icon"></i>
                    Pluja Acumulada
                </div>
                <div class="data-value">
                    {format_rain(station_data.get('total_rain'))}<span class="data-unit">mm</span>
                </div>
            </div>
        </div>
        
        <!-- PEU CORREGIT -->
        <div class="footer fade-in delay-5">
            Weather Full Screen | Font: https://www.meteo.cat/
        </div>
    </div>
    
    <script>
        // REFRESCA CADA 15 MINUTS PER NOUES DADES
        // La hora NO canvia cada minut, només quan es carreguin dades noves
        setTimeout(() => {{ 
            console.log('🔄 Refrescant per dades noves...');
            location.reload(); 
        }}, 15 * 60 * 1000); // 15 minuts
        
        // MODE TV AUTOMÀTIC
        let mouseTimer;
        const startTVMode = () => {{
            if (!document.fullscreenElement) {{
                const elem = document.documentElement;
                if (elem.requestFullscreen) elem.requestFullscreen();
                else if (elem.webkitRequestFullscreen) elem.webkitRequestFullscreen();
                else if (elem.msRequestFullscreen) elem.msRequestFullscreen();
            }}
        }};
        
        // Detecta si és TV (sense moviment de ratolí)
        document.addEventListener('mousemove', () => {{
            clearTimeout(mouseTimer);
            mouseTimer = setTimeout(startTVMode, 3000);
        }});
        
        mouseTimer = setTimeout(startTVMode, 3000);
        
        // EFECTE VISUAL EN CARRREGAR
        document.addEventListener('DOMContentLoaded', () => {{
            const boxes = document.querySelectorAll('.data-box');
            boxes.forEach((box, index) => {{
                setTimeout(() => {{
                    box.style.boxShadow = '0 0 20px rgba(255, 255, 255, 0.6)';
                    setTimeout(() => {{
                        box.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.3)';
                    }}, 400);
                }}, 150 * (index + 1));
            }});
        }});
    </script>
</body>
</html>'''
    
    return html_content

def save_html_file(content, filename):
    """Guarda el contingut HTML a un fitxer"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ HTML guardat: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error guardant HTML {filename}: {e}")
        return False

def main():
    """Funció principal - GENERA SOLAMENT 2 FITXERS"""
    
    print("=" * 60)
    print("🎨 GENERADOR HTML - VERSIÓ FINAL CORREGIDA")
    print("=" * 60)
    print("✅ CORRECCIONS APLICADES:")
    print("   1. Hora FIXA (no canvia cada minut)")
    print("   2. Font: https://www.meteo.cat/")
    print("   3. Hora d'actualització en CAT")
    print("   4. Genera SOLAMENT 2 fitxers")
    print("=" * 60)
    
    # Llegir dades
    weather_data = read_weather_summary()
    
    if not weather_data:
        print("❌ No es poden llegir les dades. Executa primer daily_weather_scraper.py")
        return False
    
    stations = weather_data.get('stations', {})
    
    if not stations:
        print("⚠️  No hi ha dades d'estacions")
        return False
    
    print(f"📊 Dades carregades. Estacions: {list(stations.keys())}")
    
    # Mapeig de codis a noms
    station_info = {
        'UO': 'Fornells de la Selva',
        'XJ': 'Girona'
    }
    
    # Diccionari per evitar noms duplicats
    generated_files = {}
    
    # Generar HTMLs - SOLAMENT ELS DOS NECESSARIS
    for station_code, data in stations.items():
        station_name = station_info.get(station_code, f"Estació {station_code}")
        
        print(f"\n📡 Processant: {station_name}")
        
        html_content = create_html_for_station(data, station_code, station_name)
        
        # NOMS DEFINITIUS I FIXOS - SOLAMENT AQUESTOS DOS
        if station_code == 'XJ':
            filename = "girona_full_screen.html"
        elif station_code == 'UO':
            filename = "fornells_full_screen.html"
        else:
            # No hauria d'arribar aquí, però per si de cas
            print(f"⚠️  Estació no reconeguda: {station_code}")
            continue
        
        # Verificar que no es generi duplicat
        if filename in generated_files:
            print(f"⚠️  Atenció: El fitxer {filename} ja s'ha generat!")
            continue
            
        if save_html_file(html_content, filename):
            generated_files[filename] = True
            print(f"✅ Generat: {filename}")
    
    # Netejar possibles fitxers antics
    print("\n" + "=" * 60)
    print("🧹 NETEGANT FITXERS ANTICS:")
    print("=" * 60)
    
    # Llista de fitxers antics a eliminar
    old_files = [
        "fornells_selva_full_screen.html",
        "fornells_de_la_selva_full_screen.html",
        "girona_full_screen_old.html",
        "weather_full_screen.html"
    ]
    
    for old_file in old_files:
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
                print(f"   ✅ Esborrat: {old_file}")
            except Exception as e:
                print(f"   ⚠️  No s'ha pogut esborrar {old_file}: {e}")
    
    # Resum final
    print("\n" + "=" * 60)
    print("✅ HTMLs GENERATS (sense duplicats):")
    print("=" * 60)
    for filename in sorted(generated_files.keys()):
        print(f"   • {filename}")
    
    print("\n🌐 URLs DEFINITIVES:")
    print("=" * 60)
    print("   📍 Girona:")
    print("      https://joandecorts.github.io/meteo-rss-auto/girona_full_screen.html")
    print("\n   📍 Fornells de la Selva:")
    print("      https://joandecorts.github.io/meteo-rss-auto/fornells_full_screen.html")
    
    print("\n🎯 CARACTERÍSTIQUES:")
    print("=" * 60)
    print("   1. ✅ Hora FIXA (la de l'actualització de les dades)")
    print("   2. ✅ No canvia cada minut")
    print("   3. ✅ Font correcta: https://www.meteo.cat/")
    print("   4. ✅ Hora d'actualització en CAT")
    print("   5. ✅ Ultra compacte i responsive")
    print("   6. ✅ Auto-pantalla completa en TV")
    
    print("\n🚀 Pujal'ls a GitHub Pages:")
    print("=" * 60)
    print("   git add girona_full_screen.html fornells_full_screen.html")
    print("   git commit -m 'Correccions: hora fixa i font meteo.cat'")
    print("   git push origin gh-pages")
    
    return True

if __name__ == "__main__":
    # Verificar que existeix el fitxer de dades
    if not os.path.exists('data/weather_summary.json'):
        print("\n❌ ERROR: No es troba data/weather_summary.json")
        print("💡 Executa abans: python daily_weather_scraper.py")
        print("\nComandaments:")
        print("   cd \"C:\\Users\\joant\\Documents\\OBS Scripts\"")
        print("   python daily_weather_scraper.py")
        print("   python generate_fullscreen_html.py")
    else:
        success = main()
        if not success:
            print("\n⚠️  El procés no s'ha completat correctament")
