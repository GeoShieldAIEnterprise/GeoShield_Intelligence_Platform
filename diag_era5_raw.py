import sys
sys.path.insert(0, ".")
import geopandas as gpd
import subprocess

COUNTIES_GEOJSON = "frontend/static/data/kenya_counties.geojson"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

counties = gpd.read_file(COUNTIES_GEOJSON)
names, lats, lons = [], [], []
for _, row in counties.iterrows():
    name = row.get("COUNTY") or row.get("NAME") or row.get("name")
    if not name:
        continue
    centroid = row.geometry.centroid
    names.append(name)
    lats.append(str(round(centroid.y, 4)))
    lons.append(str(round(centroid.x, 4)))

lat_param = ",".join(lats)
lon_param = ",".join(lons)
url = (
    f"{OPEN_METEO_URL}?latitude={lat_param}&longitude={lon_param}"
    "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,surface_pressure"
    "&timezone=auto"
)

print(f"Requesting {len(names)} counties.")
print(f"URL length: {len(url)} characters")
print()

result = subprocess.run(
    ["curl.exe", "-s", "-i", "--max-time", "30", url],  # -i includes HTTP headers/status
    capture_output=True, text=True, timeout=35,
)

print("=== curl exit code ===")
print(result.returncode)
print()
print("=== Raw response (headers + body, first 2000 chars) ===")
print(result.stdout[:2000])
