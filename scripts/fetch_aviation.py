import json
import re
from datetime import datetime, timezone
from urllib.request import urlopen

AIRPORTS = [
    {"icao": "LEGE", "name": "Girona – Costa Brava"},
    {"icao": "LEBL", "name": "Barcelona – El Prat"},
]

METAR_URL = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao}.TXT"
TAF_URL   = "https://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{icao}.TXT"


def fetch_text(url: str) -> str:
    with urlopen(url) as r:
        return r.read().decode("utf-8", errors="replace").strip()


def split_raw(txt: str):
    """
    NOAA TXT:
      línia 1: YYYY/MM/DD HH:MM
      línia 2: METAR ....
    """
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    issued = lines[0] if lines else None
    raw = " ".join(lines[1:]) if len(lines) > 1 else ""
    return issued, raw


def parse_fields(metar: str) -> dict:
    """
    Parser simple i robust per a ús visual (no operatiu).
    """
    f = {}

    # CAVOK → bon temps
    if "CAVOK" in metar:
        f["visibility_m"] = 10000
        f["ceiling_ft"] = None
        f["category"] = "VFR"

    tokens = metar.split()

    for tk in tokens:
        # Vent (dddffKT o dddffGggKT)
        m = re.match(r"^(VRB|\d{3})(\d{2})(G(\d{2}))?KT$", tk)
        if m:
            f["wind"] = {
                "dir": m.group(1),
                "speed_kt": int(m.group(2)),
                "gust_kt": int(m.group(4)) if m.group(4) else None
            }

        # Visibilitat (9999)
        if tk.isdigit() and len(tk) == 4 and "visibility_m" not in f:
            v = int(tk)
            if 0 < v <= 9999:
                f["visibility_m"] = v

        # QNH
        if tk.startswith("Q") and tk[1:].isdigit():
            f["qnh_hpa"] = int(tk[1:])

        # Temperatura / punt de rosada
        if "/" in tk and tk.replace("/", "").replace("M", "").isdigit():
            t, td = tk.split("/")
            f["temp_c"] = -int(t[1:]) if t.startswith("M") else int(t)
            f["dewpoint_c"] = -int(td[1:]) if td.startswith("M") else int(td)

        # Núvols
        if tk.startswith(("BKN", "OVC")) and tk[3:].isdigit():
            ft = int(tk[3:]) * 100
            current = f.get("ceiling_ft")
            f["ceiling_ft"] = ft if current is None else min(current, ft)

    # Categoria si no és CAVOK
    ceil = f.get("ceiling_ft")
    vis = f.get("visibility_m")

    if "category" not in f:
        if ceil is not None and ceil < 500:
            f["category"] = "LIFR"
        elif ceil is not None and ceil < 1000:
            f["category"] = "IFR"
        elif ceil is not None and ceil < 3000:
            f["category"] = "MVFR"
        elif vis is not None and vis < 1600:
            f["category"] = "LIFR"
        elif vis is not None and vis < 4800:
            f["category"] = "IFR"
        elif vis is not None and vis < 8000:
            f["category"] = "MVFR"
        else:
            f["category"] = "VFR"

    return f


output = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "airports": []
}

for a in AIRPORTS:
    metar_txt = fetch_text(METAR_URL.format(icao=a["icao"]))
    taf_txt   = fetch_text(TAF_URL.format(icao=a["icao"]))

    metar_issued, metar_raw = split_raw(metar_txt)
    taf_issued, taf_raw     = split_raw(taf_txt)

    fields = parse_fields(metar_raw)

    output["airports"].append({
        "icao": a["icao"],
        "name": a["name"],
        "metar": {
            "issued": metar_issued,
            "raw": metar_raw,
            "fields": fields
        },
        "taf": {
            "issued": taf_issued,
            "raw": taf_raw
        }
    })

with open("data/aviation.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
``
