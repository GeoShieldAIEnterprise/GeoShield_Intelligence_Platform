import io

path = "frontend/templates/index.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

replacements = {
    "Overall Risk": "\U0001F6E1\uFE0F",
    "Highest Flood Risk County": "\U0001F30A",
    "Flash Flood Watch Counties (hot + bare soil)": "\u26A1",
    "El Ni\u00f1o Monitoring": "\U0001F30E",
    "Hotspot intensity:": "\U0001F525",
    "Live VIIRS Hotspots (Kenya-wide)": "\U0001F525",
    "Highest Fire Risk County (dry vegetation)": "\U0001F525",
    "Live Temperature (ERA5)": "\U0001F321\uFE0F",
    "Live Earthquakes (past 24h, magnitude 4.0+)": "\U0001F30D",
    "Population Exposed (50km radius)": "\U0001F465",
    "Highest Drought Risk County": "\U0001F3DC\uFE0F",
    "GPM Precipitation / ERA5 Climate": "\U0001F327\uFE0F",
}

fixed_count = 0
for label, emoji in replacements.items():
    broken = "? " + label
    if broken in content:
        content = content.replace(broken, emoji + " " + label)
        fixed_count += 1
    else:
        print(f"NOT FOUND as '?  {label}' -- may need a different placeholder count (??, ???) or already fixed.")

with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print(f"\nFixed {fixed_count} of {len(replacements)} labels.")
