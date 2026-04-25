import json
from datetime import datetime, timezone
from urllib.request import urlopen

AIRPORTS = [
    {"icao": "LEGE", "name": "Girona – Costa Brava"},
    {"icao": "LEBL", "name": "Barcelona – El Prat"},
]

METAR_URL = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao}.TXT"
TAF_URL   = "https://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{icao}.TXT"

def fetch_text(url):
    with urlopen(url) as r:
        return r.read().decode("utf-8", errors="replace").strip()

def split_raw(txt):
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    issued = lines[0] if lines else None
    raw = " ".join(lines[1:]) if len(lines) > 1 else ""
    return issued, raw

out = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "airports": []
}

for a in AIRPORTS:
    metar_txt = fetch_text(METAR_URL.format(icao=a["icao"]))
    taf_txt   = fetch_text(TAF_URL.format(icao=a["icao"]))

    metar_issued, metar_raw = split_raw(metar_txt)
    taf_issued, taf_raw     = split_raw(taf_txt)

    out["airports"].append({
        "icao": a["icao"],
        "name": a["name"],
        "metar": {
            "issued": metar_issued,
            "raw": metar_raw,
            "fields": {}
        },
        "taf": {
            "issued": taf_issued,
            "raw": taf_raw
        }
    })

with open("data/aviation.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
