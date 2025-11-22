import requests
import json
from datetime import datetime
import os
import glob
import pytz

def fetch_station_data(station_code):
    """Fetches weather data for a specific station"""
    url = f"https://api.meteo.cat/xema/v1/estacions/{station_code}/variables/32/ultimes/1"
    
    headers = {
        'User-Agent': 'MeteoCat-RSS-Bot/1.0 (https://github.com/joandecoris/meteo-rss-auto)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            return data[0]
        else:
            print(f"No data found for station {station_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {station_code}: {e}")
        return None

def get_current_station():
    """Alterna entre estacions basant-se en el minut actual"""
    current_minute = datetime.now().minute
    # Si el minut és parell: Girona, si és senar: Fornells
    if current_minute % 2 == 0:
        return {"code": "XJ", "name": "Girona"}
    else:
        return {"code": "UO", "name": "Fornells de la Selva"}

def generate_rss_feed():
    """Generate RSS feed from the latest weather data"""
    # Trobar tots els fitxers de dades
    weather_files = glob.glob("weather-data/weather_data_*.json")
    if not weather_files:
        print("No weather data files found")
        return
    
    # Agafar els 2 fitxers més recents (per tenir les dues estacions)
    latest_files = sorted(weather_files, key=os.path.getctime, reverse=True)[:2]
    
    all_weather_data = []
    
    for file_path in latest_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    all_weather_data.extend(data)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    if not all_weather_data:
        print("No weather data available")
        return
    
    # Configuració de fus horari
    tz = pytz.timezone('Europe/Madrid')
    
    # Generar items RSS per cada estació
    items = []
    
    for weather_data in all_weather_data:
        station_name = weather_data.get("station_name", "Unknown Station")
        station_code = weather_data.get("station_code", "Unknown")
        
        data = weather_data.get("data", [{}])[0] if weather_data.get("data") else {}
        valor = data.get("valor")
        data_lectura = data.get("data")
        
        if valor is not None and data_lectura:
            try:
                # Convertir la data
                lectura_dt = datetime.fromisoformat(data_lectura.replace('Z', '+00:00'))
                lectura_dt = lectura_dt.astimezone(tz)
                data_legible = lectura_dt.strftime("%d/%m/%Y %H:%M:%S")
                
                title = f"🌡️ {station_name}: {valor}°C"
                description = f"Temperatura a {station_name} ({station_code}): {valor}°C - Actualitzat: {data_legible}"
                
                item = f"""    <item>
        <title><![CDATA[{title}]]></title>
        <description><![CDATA[{description}]]></description>
        <pubDate>{lectura_dt.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
        <guid>{station_code}_{data_lectura}</guid>
    </item>"""
                
                items.append(item)
                
            except Exception as e:
                print(f"Error processing data for {station_name}: {e}")
                continue
    
    if not items:
        print("No valid weather data to generate RSS")
        return
    
    # Generar el RSS feed complet
    current_time = datetime.now(tz).strftime("%a, %d %b %Y %H:%M:%S %z")
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>MeteoCat Weather Stations</title>
    <description>Temperatures de les estacions meteorològiques de Girona i Fornells de la Selva</description>
    <link>https://github.com/joandecoris/meteo-rss-auto</link>
    <lastBuildDate>{current_time}</lastBuildDate>
    <pubDate>{current_time}</pubDate>
    <ttl>10</ttl>
{chr(10).join(items)}
</channel>
</rss>"""
    
    # Guardar el fitxer RSS
    with open("meteo.rss", "w", encoding="utf-8") as f:
        f.write(rss_content)
    
    print(f"RSS feed generated successfully with {len(items)} stations")

def main():
    # Triem quina estació consultar en aquesta execució
    station = get_current_station()
    print(f"Fetching data for {station['name']} ({station['code']})...")
    
    station_data = fetch_station_data(station["code"])
    
    if station_data:
        # Afegim informació de l'estació
        station_data["station_name"] = station["name"]
        station_data["station_code"] = station["code"]
        
        # Guardem les dades
        output_dir = "weather-data"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/weather_data_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([station_data], f, ensure_ascii=False, indent=2)
        
        print(f"Weather data saved to {output_file}")
        print(f"Successfully fetched data for {station['name']}")
        
        # Generar el RSS feed amb les dades recopilades
        generate_rss_feed()
    else:
        print(f"No data fetched for {station['name']}")
        # Exit with error code to fail the workflow
        exit(1)

if __name__ == "__main__":
    main()
