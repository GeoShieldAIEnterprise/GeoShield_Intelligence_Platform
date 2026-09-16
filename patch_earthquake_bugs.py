from pathlib import Path

def patch(path_str, anchor, addition, label):
    path = Path(path_str)
    src = path.read_text(encoding="utf-8-sig")
    original = src
    if anchor not in src:
        raise SystemExit(f"ERROR: anchor not found for {label} in {path_str} -- printing file:\n" + src)
    src = src.replace(anchor, addition, 1)
    if src == original:
        print(f"{label}: no changes were necessary.")
    else:
        path.write_text(src, encoding="utf-8", newline="\n")
        print(f"{label}: patched successfully.")

# ------------------------------------------------------------
# 1. population_connector.py -- URL-encode the geojson query param
# ------------------------------------------------------------

patch(
    "core/connectors/population_connector.py",
    "import json\nimport math\nimport subprocess\nimport time\nfrom typing import Any",
    "import json\nimport math\nimport subprocess\nimport time\nimport urllib.parse\nfrom typing import Any",
    "population_connector.py (import urllib.parse)",
)

patch(
    "core/connectors/population_connector.py",
    '        geojson = json.dumps(_circle_polygon(lat, lon, radius_km))\n'
    '        url = f"{WORLDPOP_STATS_URL}?dataset=wpgppop&year={year}&geojson={geojson}&runasync=false"',
    '        geojson = json.dumps(_circle_polygon(lat, lon, radius_km))\n'
    '        url = f"{WORLDPOP_STATS_URL}?dataset=wpgppop&year={year}&geojson={urllib.parse.quote(geojson)}&runasync=false"',
    "population_connector.py (URL-encode geojson param)",
)

# ------------------------------------------------------------
# 2. event_enrichment.py -- sanitize NaN road fields before returning
# ------------------------------------------------------------

patch(
    "core/event_enrichment.py",
    '        if county.empty:\n'
    '            county_name = "Unknown"\n'
    '        else:\n'
    '            county_name = county["COUNTY"].iloc[0]\n'
    '\n'
    '        return {\n'
    '\n'
    '            "longitude": longitude,\n'
    '\n'
    '            "latitude": latitude,\n'
    '\n'
    '            "county": county_name,\n'
    '\n'
    '            "road_type": road["RTT_DESCRI"],\n'
    '\n'
    '            "road_surface": road["MED_DESCRI"]\n'
    '\n'
    '        }',

    '        if county.empty:\n'
    '            county_name = "Unknown"\n'
    '        else:\n'
    '            county_name = county["COUNTY"].iloc[0]\n'
    '\n'
    '        road_type = road["RTT_DESCRI"]\n'
    '        road_surface = road["MED_DESCRI"]\n'
    '\n'
    '        if isinstance(road_type, float) and road_type != road_type:\n'
    '            road_type = None\n'
    '        if isinstance(road_surface, float) and road_surface != road_surface:\n'
    '            road_surface = None\n'
    '\n'
    '        return {\n'
    '\n'
    '            "longitude": longitude,\n'
    '\n'
    '            "latitude": latitude,\n'
    '\n'
    '            "county": county_name,\n'
    '\n'
    '            "road_type": road_type,\n'
    '\n'
    '            "road_surface": road_surface\n'
    '\n'
    '        }',
    "event_enrichment.py (NaN-safe road fields)",
)

print()
print("ALL FIXES APPLIED -- restart uvicorn and re-test.")
