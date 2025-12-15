from datetime import datetime
import pytz
import json
import os

def write_log(message):
    print(message)
    with open('debug_dayly.log', 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def llegir_acumulacio_estacio(codi_estacio):
    """Llegeix les dades acumulades d'una estació per al dia d'avui"""
    fitxer = f"acumulacio_{codi_estacio}.json"
    
    if os.path.exists(fitxer):
        try:
            with open(fitxer, 'r', encoding='utf-8') as f:
                dades = json.load(f)
            
            data_guardada = dades.get('data', '')
            data_avui = datetime.now().strftime('%Y-%m-%d')
            
            if data_guardada == data_avui:
                return dades
            else:
                return {
                    'data': data_avui, 
                    'estacio': codi_estacio,
                    'maximes_periodes': [],
                    'minimes_periodes': [], 
                    'pluja_periodes': []
                }
                
        except Exception as e:
            write_log(f"⚠️ Error llegint {fitxer}: {e}")
    
    data_avui = datetime.now().strftime('%Y-%m-%d')
    return {
        'data': data_avui, 
        'estacio': codi_estacio,
        'maximes_periodes': [],
        'minimes_periodes': [], 
        'pluja_periodes': []
    }

def calcular_resums_estacio(codi_estacio):
    """Calcula els resums (màxima, mínima, pluja) del dia a partir de les dades acumulades"""
    dades = llegir_acumulacio_estacio(codi_estacio)
    
    maximes = dades.get('maximes_periodes', [])
    minimes = dades.get('minimes_periodes', [])
    pluja = dades.get('pluja_periodes', [])
    
    resums = {
        'data': dades.get('data', ''),
        'estacio': dades.get('estacio', '')
    }
    
    if maximes:
        resums['maxima_dia'] = round(max(maximes), 1)
        resums['num_periodes_max'] = len(maximes)
    else:
        resums['maxima_dia'] = None
        resums['num_periodes_max'] = 0
    
    if minimes:
        resums['minima_dia'] = round(min(minimes), 1)
        resums['num_periodes_min'] = len(minimes)
    else:
        resums['minima_dia'] = None
        resums['num_periodes_min'] = 0
    
    if pluja:
        resums['pluja_dia'] = round(sum(pluja), 1)
        resums['num_periodes_pluja'] = len(pluja)
    else:
        resums['pluja_dia'] = None
        resums['num_periodes_pluja'] = 0
    
    return resums

def generar_rss_diari():
    write_log("\n🚀 GENERANT RSS DIARI (A PARTIR D'ACUMULACIÓ LOCAL)")
    
    cet = pytz.timezone('CET')
    now = datetime.now(cet)
    data_avui = now.strftime('%Y-%m-%d')
    
    estacions = [
        {"code": "XJ", "name": "Girona"},
        {"code": "UO", "name": "Fornells de la Selva"}
    ]
    
    entrades = []
    
    for station in estacions:
        write_log(f"\n📊 Calculant resums per {station['name']}")
        resum = calcular_resums_estacio(station['code'])
        
        if resum.get('maxima_dia') is not None:
            # VERSIÓ CATALÀ - RESUM DIARI
            titol_cat = f"📊 RESUM DEL DIA {station['name']} | Data: {data_avui} | Període: 00:00-24:00 | 🔥 Temperatura Màxima: {resum['maxima_dia']}°C | ❄️ Temperatura Mínima: {resum['minima_dia']}°C | 🌧️ Pluja Acumulada: {resum['pluja_dia']}mm | 📈 Períodes processats: {resum.get('num_periodes_max', 0)}"
            
            # VERSIÓ ANGLÈS - RESUM DIARI
            titol_en = f"📊 TODAY'S SUMMARY {station['name']} | Date: {data_avui} | Period: 00:00-24:00 | 🔥 Maximum Temperature: {resum['maxima_dia']}°C | ❄️ Minimum Temperature: {resum['minima_dia']}°C | 🌧️ Accumulated Rain: {resum['pluja_dia']}mm | 📈 Periods processed: {resum.get('num_periodes_max', 0)}"
            
            titol = f"{titol_cat} || {titol_en}"
            
            # URL per al resum diari (pàgina del dia actual)
            link_resum = f"https://www.meteo.cat/observacions/xema/dades?codi={station['code']}"
            
            entrada = f'''  <item>
    <title>{titol}</title>
    <link>{link_resum}</link>
    <description>Resum diari de {station['name']} - Data: {data_avui} - Actualitzat a les {now.strftime('%H:%M')} CET / Daily summary from {station['name']} - Date: {data_avui} - Updated at {now.strftime('%H:%M')} CET</description>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</pubDate>
  </item>'''
            
            entrades.append(entrada)
            write_log(f"✅ Resum generat: Màx={resum['maxima_dia']}°C, Mín={resum['minima_dia']}°C, Pluja={resum['pluja_dia']}mm, Períodes={resum.get('num_periodes_max', 0)}")
        else:
            write_log(f"⚠️ Sense dades acumulades per {station['name']}")
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>MeteoCat Resums Diaris (Acumulació Local)</title>
  <link>https://www.meteo.cat</link>
  <description>Resums meteorològics basats en dades acumulades localment - Estacions Girona i Fornells de la Selva / Weather summaries based on locally accumulated data - Girona and Fornells de la Selva stations</description>
  <lastBuildDate>{now.strftime("%a, %d %b %Y %H:%M:%S CET")}</lastBuildDate>
{chr(10).join(entrades)}
</channel>
</rss>'''
    
    try:
        with open('update_meteo_dayly.rss', 'w', encoding='utf-8') as f:
            f.write(rss_content)
        write_log("✅ RSS diari generat correctament (a partir d'acumulació local)")
        write_log(f"📁 Arxiu: update_meteo_dayly.rss")
        return True
    except Exception as e:
        write_log(f"❌ Error guardant RSS diari: {e}")
        return False

if __name__ == "__main__":
    with open('debug_dayly.log', 'w', encoding='utf-8') as f:
        f.write(f"=== INICI RSS DIARI: {datetime.now()} ===\n")
    
    write_log("🚀 Script de resums diaris (acumulació local)")
    
    try:
        exit = generar_rss_diari()
        if exit:
            write_log("🎉 Èxit complet - RSS diari generat")
        else:
            write_log("💤 Fallada en la generació del RSS diari")
    except Exception as e:
        write_log(f"💥 ERROR: {e}")
        import traceback
        write_log(f"📋 Traceback: {traceback.format_exc()}")
        exit = False
    
    write_log(f"=== FI RSS DIARI: {datetime.now()} ===")
