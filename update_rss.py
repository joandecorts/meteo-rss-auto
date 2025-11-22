def generar_rss():
    write_log("\n" + "="*60)
    write_log("🚀 INICIANT GENERACIÓ RSS")
    
    # Triem quina estació consultar
    station = get_current_station()
    write_log(f"🎯 ESTACIÓ SELECCIONADA: {station['name']} [{station['code']}]")
    
    dades = get_meteo_data(station['code'], station['name'])
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES")
        write_log("💤 NO S'ACTUALITZA RSS")
        return False
    
    write_log("✅ DADES OBTINGUDES - GENERANT RSS")
    
    # Títol complet amb TOTES les dades disponibles
    titol_cat = (
        f"🌤️ {dades['station_name']} | Actualitzat: {current_time} | Període: {dades['periode']} | "
        f"Temp. Mitjana: {dades['tm']}°C | Temp. Màxima: {dades['tx']}°C | Temp. Mínima: {dades['tn']}°C | "
        f"Humitat: {dades['hr']}% | Precipitació: {dades['ppt']}mm | "
        f"Vent Mitjà: {dades['vvm']}km/h | Direcció Vent: {dades['dvm']}° | "
        f"Vent Màxim: {dades['vvx']}km/h | Pressió: {dades['pm']}hPa | "
        f"Radiació Solar: {dades['rs']}W/m²"
    )
    
    titol_en = (
        f"🌤️ {dades['station_name']} | Updated: {current_time} | Period: {dades['periode']} | "
        f"Avg Temp: {dades['tm']}°C | Max Temp: {dades['tx']}°C | Min Temp: {dades['tn']}°C | "
        f"Humidity: {dades['hr']}% | Precipitation: {dades['ppt']}mm | "
        f"Avg Wind: {dades['vvm']}km/h | Wind Direction: {dades['dvm']}° | "
        f"Max Wind: {dades['vvx']}km/h | Pressure: {dades['pm']}hPa | "
        f"Solar Radiation: {dades['rs']}W/m²"
    )
    
    titol = f"{titol_cat} || {titol_en}"
    
    write_log(f"📝 Títol generat ({len(titol)} caràcters)")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Weather Stations</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estacions Girona i Fornells de la Selva</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat/observacions/xema/dades?codi={dades['station_code']}</link>
    <description>Dades meteorològiques automàtiques de l'estació de {dades['station_name']} ({dades['station_code']})</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    write_log("📁 Intentant escriure el fitxer meteo.rss...")
    
    try:
        with open('meteo.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        write_log("✅ RSS guardat a 'meteo.rss'")
        return True
        
    except Exception as e:
        write_log(f"❌ ERROR escrivint el fitxer: {str(e)}")
        return False
