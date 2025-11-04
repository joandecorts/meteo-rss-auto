def generar_rss():
    write_log("\n" + "="*60)
    write_log("🚀 INICIANT GENERACIÓ RSS")
    
    dades = get_meteo_data()
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    current_time = now.strftime("%H:%M")
    
    if not dades:
        write_log("❌ NO S'HAN POGUT OBTENIR DADES")
        write_log("💤 NO S'ACTUALITZA RSS")
        return False
    
    write_log("✅ DADES OBTINGUDES - GENERANT RSS")
    
    # FORMAT MILLORAT - CATALÀ amb descripcions clares
    titol_cat = (
        f"🌤️ GIRONA | Actualitzat: {current_time} | Període: {dades['periode']} | "
        f"Temp. Mitjana: {dades['tm']}°C | Temp. Màxima: {dades['tx']}°C | Temp. Mínima: {dades['tn']}°C | "
        f"Humitat: {dades['hr']}% | Precipitació: {dades['ppt']}mm | "
        f"Vent Mitjà: {dades['vvm']}km/h | Direcció Vent: {dades['dvm']}° | "
        f"Vent Màxim: {dades['vvx']}km/h | Pressió: {dades['pm']}hPa | "
        f"Radiació Solar: {dades['rs']}W/m²"
    )
    
    # FORMAT MILLORAT - ANGLÈS amb descripcions clares
    titol_en = (
        f"🌤️ GIRONA | Updated: {current_time} | Period: {dades['periode']} | "
        f"Avg Temp: {dades['tm']}°C | Max Temp: {dades['tx']}°C | Min Temp: {dades['tn']}°C | "
        f"Humidity: {dades['hr']}% | Precipitation: {dades['ppt']}mm | "
        f"Avg Wind: {dades['vvm']}km/h | Wind Direction: {dades['dvm']}° | "
        f"Max Wind: {dades['vvx']}km/h | Pressure: {dades['pm']}hPa | "
        f"Solar Radiation: {dades['rs']}W/m²"
    )
    
    # COMBINAR AMB SEPARACIÓ CLARA
    titol = f"{titol_cat} || {titol_en}"
    
    write_log(f"📝 Títol generat ({len(titol)} caràcters)")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Girona</title>
  <link>https://www.meteo.cat</link>
  <description>Dades meteorològiques en temps real - Estació Girona [XJ] - Real-time weather data</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
  <item>
    <title>{titol}</title>
    <link>https://www.meteo.cat/observacions/xema/dades?codi=XJ</link>
    <description>Dades meteorològiques automàtiques de l'estació de Girona (XJ) - Automatic weather data from Girona station (XJ)</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>
</channel>
</rss>'''
    
    with open('meteo.rss', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    write_log("✅ RSS guardat a 'meteo.rss'")
    
    return True
