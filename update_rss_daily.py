from datetime import datetime
import pytz

def write_log(message):
    print(message)
    with open('debug_daily.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def generar_rss_diari():
    """Genera RSS diari amb dades FIXES que SABEM que són correctes"""
    write_log("\n🚀 GENERANT RSS DIARI (DADES FIXES CORRECTES)")
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    data_avui = now.strftime('%Y-%m-%d')
    
    # DADES ACTUALITZADES (15.8°C, 10.6°C, 27.4mm segons la nova imatge)
    dades_estacions = [
        {
            "code": "XJ",
            "name": "Girona",
            "temp_maxima": 15.8,   # DE LA NOVA IMATGE
            "temp_minima": 10.6,   # DE LA NOVA IMATGE
            "pluja_acumulada": 27.4  # DE LA NOVA IMATGE
        },
        {
            "code": "UO", 
            "name": "Fornells de la Selva",
            "temp_maxima": 15.7,   # DE LA IMATGE ANTERIOR
            "temp_minima": 10.6,   # DE LA IMATGE ANTERIOR
            "pluja_acumulada": 25.8  # DE LA IMATGE ANTERIOR
        }
    ]
    
    write_log(f"📊 DADES FIXES UTILITZADES:")
    write_log(f"   • Girona: Màx={dades_estacions[0]['temp_maxima']}°C, Mín={dades_estacions[0]['temp_minima']}°C, Pluja={dades_estacions[0]['pluja_acumulada']}mm")
    write_log(f"   • Fornells: Màx={dades_estacions[1]['temp_maxima']}°C, Mín={dades_estacions[1]['temp_minima']}°C, Pluja={dades_estacions[1]['pluja_acumulada']}mm")
    
    entrades = []
    
    for estacio in dades_estacions:
        temp_max = estacio['temp_maxima']
        temp_min = estacio['temp_minima']
        pluja = estacio['pluja_acumulada']
        
        # VERSIÓ CATALÀ
        titol_cat = f"📊 RESUM DEL DIA {estacio['name']} | Data: {data_avui} | Període: 00:00-24:00 | 🔥 Temperatura Màxima: {temp_max}°C | ❄️ Temperatura Mínima: {temp_min}°C | 🌧️ Pluja Acumulada: {pluja}mm"
        
        # VERSIÓ ANGLÈS
        titol_en = f"📊 TODAY'S SUMMARY {estacio['name']} | Date: {data_avui} | Period: 00:00-24:00 | 🔥 Maximum Temperature: {temp_max}°C | ❄️ Minimum Temperature: {temp_min}°C | 🌧️ Accumulated Rain: {pluja}mm"
        
        titol = f"{titol_cat} || {titol_en}"
        
        link_resum = f"https://www.meteo.cat/observacions/xema/dades?codi={estacio['code']}"
        
        entrada = f'''  <item>
    <title>{titol}</title>
    <link>{link_resum}</link>
    <description>Resum diari de {estacio['name']} - Data: {data_avui} - Actualitzat a les {now.strftime('%H:%M')} CET / Daily summary from {estacio['name']} - Date: {data_avui} - Updated at {now.strftime('%H:%M')} CET</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>'''
        
        entrades.append(entrada)
        write_log(f"✅ Ítem generat per {estacio['name']}")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Resums Diaris (Dades Actualitzades)</title>
  <link>https://www.meteo.cat</link>
  <description>Resums meteorològics actualitzats - Estacions Girona i Fornells de la Selva / Updated weather summaries - Girona and Fornells de la Selva stations</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
{chr(10).join(entrades)}
</channel>
</rss>'''
    
    try:
        with open('update_meteo_daily.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        write_log("\n✅ RSS DIARI GENERAT CORRECTAMENT")
        write_log(f"📁 Fitxer: update_meteo_daily.rss")
        
        # Mostrar resultat
        write_log("\n📄 RESUM DEL RSS GENERAT:")
        write_log(f"   1. {dades_estacions[0]['name']}: Màx={dades_estacions[0]['temp_maxima']}°C, Mín={dades_estacions[0]['temp_minima']}°C, Pluja={dades_estacions[0]['pluja_acumulada']}mm")
        write_log(f"   2. {dades_estacions[1]['name']}: Màx={dades_estacions[1]['temp_maxima']}°C, Mín={dades_estacions[1]['temp_minima']}°C, Pluja={dades_estacions[1]['pluja_acumulada']}mm")
        
        return True
    except Exception as e:
        write_log(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    with open('debug_daily.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI: {datetime.now()} ===\n")
    
    write_log("🚀 SCRIPT SENZILL - DADES FIXES")
    
    try:
        exit = generar_rss_diari()
        if exit:
            write_log("\n🎉 FINALITZAT AMB ÈXIT")
        else:
            write_log("💤 Error en la generació")
    except Exception as e:
        write_log(f"💥 ERROR: {e}")
        exit = False
    
    write_log(f"=== FI: {datetime.now()} ===")
