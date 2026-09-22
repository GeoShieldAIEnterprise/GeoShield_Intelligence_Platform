labels = [
    "Overall Risk",
    "Highest Flood Risk County",
    "Flash Flood Watch Counties (hot + bare soil)",
    "El Ni\u00f1o Monitoring",
    "Hotspot intensity:",
    "Live VIIRS Hotspots (Kenya-wide)",
    "Highest Fire Risk County (dry vegetation)",
    "Live Temperature (ERA5)",
    "Live Earthquakes (past 24h, magnitude 4.0+)",
    "Population Exposed (50km radius)",
    "Highest Drought Risk County",
    "GPM Precipitation / ERA5 Climate",
]

with open("frontend/templates/index.html", "rb") as f:
    content = f.read().decode("utf-8")

for label in labels:
    idx = content.find(label)
    if idx == -1:
        print(f"NOT FOUND AT ALL: {label!r}")
        continue
    start = max(0, idx - 25)
    before = content[start:idx]
    print(f"{label!r}")
    print(f"  preceding 25 chars: {before!r}")
    print()
