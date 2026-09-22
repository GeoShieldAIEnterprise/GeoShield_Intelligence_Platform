path = "frontend/templates/index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

replacements = {
    "?\U0001F6E1\uFE0F Overall Risk": "\U0001F6E1\uFE0F Overall Risk",
    "?\U0001F30A Highest Flood Risk County": "\U0001F30A Highest Flood Risk County",
    "?\U0001F30E El Ni\u00f1o Monitoring": "\U0001F30E El Ni\u00f1o Monitoring",
    "?\U0001F525 Hotspot intensity:": "\U0001F525 Hotspot intensity:",
    "?\U0001F525 Live VIIRS Hotspots (Kenya-wide)": "\U0001F525 Live VIIRS Hotspots (Kenya-wide)",
    "?\U0001F525 Highest Fire Risk County (dry vegetation)": "\U0001F525 Highest Fire Risk County (dry vegetation)",
    "??\U0001F321\uFE0F Live Temperature (ERA5)": "\U0001F321\uFE0F Live Temperature (ERA5)",
    "?\U0001F30D Live Earthquakes (past 24h, magnitude 4.0+)": "\U0001F30D Live Earthquakes (past 24h, magnitude 4.0+)",
    "?\U0001F465 Population Exposed (50km radius)": "\U0001F465 Population Exposed (50km radius)",
    "?\U0001F3DC\uFE0F Highest Drought Risk County": "\U0001F3DC\uFE0F Highest Drought Risk County",
    "??\U0001F327\uFE0F GPM Precipitation / ERA5 Climate": "\U0001F327\uFE0F GPM Precipitation / ERA5 Climate",
}

total_fixed = 0
for broken, clean in replacements.items():
    count = content.count(broken)
    if count:
        content = content.replace(broken, clean)
        total_fixed += count
        print(f"Fixed {count}x: {clean!r}")
    else:
        print(f"NOT FOUND (already clean or different context): {broken!r}")

with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nTotal replacements made: {total_fixed}")
