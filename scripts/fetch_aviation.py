#!/usr/bin/env python3
import json, re
from datetime import datetime, timezone
from urllib.request import urlopen, Request

AIRPORTS = [
    {"icao": "LEGE", "name": "Girona – Costa Brava"},
    {"icao": "LEBL", "name": "Barcelona – El Prat"},
]

METAR_URL = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao}.TXT"
TAF_URL   = "https://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{icao}.TXT"

def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "metar-obs/1.0 (github actions)"})
    with urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace").strip()

def parse_metar_raw(txt: str):
    # NOAA .TXT normalment:
    # line1: YYYY/MM/DD HH:MM
    # line2: METAR ...
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    issued = lines[0] if lines else None
    raw = " ".join(lines[1:2]) if len(lines) >= 2 else (lines[0] if lines else "")
    return issued, raw

def parse_taf_raw(txt: str):
    lines = [l.rstrip() for l in txt.splitlines() if l.strip()]
    issued = lines[0] if lines else None
    raw = "\n".join(lines[1:]) if len(lines) >= 2 else (lines[0] if lines else "")
    return issued, raw

def parse_basic_fields(metar: str):
    # Vent: dddff(Ggg)KT
    m_wind = re.search(r"\b(\d{3}|VRB)(\d{2,3})(G(\d{2,3}))?KT\b", metar)
    wind = None
    if m_wind:
        wind = {
            "dir": m_wind.group(1),
            "speed_kt": int(m_wind.group(2)),
            "gust_kt": int(m_wind.group(4)) if m_wind.group(4) else None
        }

    # Visibilitat:
    # - CAVOK -> >=10km i ceil none (en termes pràctics)
    # - 9999 -> 10km+
    # - #### metres
    vis_m = None
    if "CAVOK" in metar:
        vis_m = 10000
    else:
        m_vis = re.search(r"\b(\d{4})\b", metar)
        if m_vis:
            v = int(m_vis.group(1))
            if 0 < v <= 9999:
                vis_m = v

    # Núvols: FEW/SCT/BKN/OVC### (hundreds of feet)
    layers = re.findall(r"\b(FEW|SCT|BKN|OVC)(\d{3})\b", metar)
    ceiling_ft = None
    for cov, h in layers:
        if cov in ("BKN", "OVC"):
            ft = int(h) * 100
            ceiling_ft = ft if ceiling_ft is None else min(ceiling_ft, ft)
    if "CAVOK" in metar:
        ceiling_ft = None

    # Temp / dew: 18/10, M02/M05
    m_td = re.search(r"\b(M?\d{2})/(M?\d{2})\b", metar)
    temp_c = dew_c = None
    if m_td:
        def t(x): return -int(x[1:]) if x.startswith("M") else int(x)
        temp_c = t(m_td.group(1))
        dew_c  = t(m_td.group(2))

    # QNH: Q1019
    m_qnh = re.search(r"\bQ(\d{4})\b", metar)
    qnh_hpa = int(m_qnh.group(1)) if m_qnh else None

    # Categoria VFR simple (ceiling/vis)
    # vis en metres: MVFR < 8000? (aprox), IFR < 4800, LIFR < 1600; és aproximació.
    cat = "VFR"
    if ceiling_ft is not None and ceiling_ft < 500:
        cat = "LIFR"
    elif ceiling_ft is not None and ceiling_ft < 1000:
        cat = "IFR"
    elif ceiling_ft is not None and ceiling_ft < 3000:
        cat = "MVFR"
    elif vis_m is not None and vis_m < 1600:
        cat = "LIFR"
    elif vis_m is not None and vis_m < 4800:
        cat = "IFR"
    elif vis_m is not None and vis_m < 8000:
        cat = "MVFR"

    return {
        "wind": wind,
        "visibility_m": vis_m,
        "ceiling_ft": ceiling_ft,
        "temp_c": temp_c,
        "dewpoint_c": dew_c,
        "qnh_hpa": qnh_hpa,
        "category": cat
    }

def main():
    out = {
        "source": {
            "name": "NOAA / NWS Telecommunications Gateway (tgftp.nws.noaa.gov)",
            "metar_base": "https://tgftp.nws.noaa.gov/data/observations/metar/stations/",
            "taf_base":   "https://tgftp.nws.noaa.gov/data/forecasts/taf/stations/"
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "airports": []
    }

    for a in AIRPORTS:
        icao = a["icao"]
        metar_txt = fetch_text(METAR_URL.format(icao=icao))
        taf_txt   = fetch_text(TAF_URL.format(icao=icao))

        metar_issued, metar_raw = parse_metar_raw(metar_txt)
        taf_issued, taf_raw     = parse_taf_raw(taf_txt)

        fields = parse_basic_fields(metar_raw)

        out["airports"].append({
            "icao": icao,
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
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
``
