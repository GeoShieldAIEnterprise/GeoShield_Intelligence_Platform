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

FILE = "frontend/static/earthquakeengine.js"

# 1. Add countyLayer to state
patch(
    FILE,
    '    map: null,\n'
    '    satelliteLayer: null,\n'
    '    streetLayer: null,\n'
    '    quakeLayer: null,\n'
    '    initialized: false,',

    '    map: null,\n'
    '    satelliteLayer: null,\n'
    '    streetLayer: null,\n'
    '    countyLayer: null,\n'
    '    quakeLayer: null,\n'
    '    initialized: false,',
    "earthquakeengine.js (add countyLayer state)",
)

# 2. Call the new loader alongside the existing ones in init()
patch(
    FILE,
    '            this.loadSatelliteLayer();\n'
    '            this.loadLiveEarthquakes();',

    '            this.loadSatelliteLayer();\n'
    '            this.loadCountyOutlineLayer();\n'
    '            this.loadLiveEarthquakes();',
    "earthquakeengine.js (call loadCountyOutlineLayer in init)",
)

# 3. Add the county outline loader itself, right before loadSatelliteLayer
patch(
    FILE,
    '    async loadSatelliteLayer() {',

    '    async loadCountyOutlineLayer() {\n'
    '        try {\n'
    '            const res = await fetch("/static/data/kenya_counties.geojson");\n'
    '            const data = await res.json();\n'
    '\n'
    '            this.countyLayer = L.geoJSON(data, {\n'
    '                style: () => ({\n'
    '                    color: "#55ffff",\n'
    '                    weight: 1,\n'
    '                    fillColor: "#55ffff",\n'
    '                    fillOpacity: 0.03\n'
    '                }),\n'
    '                onEachFeature: (feature, layer) => {\n'
    '                    const county = feature.properties.COUNTY || feature.properties.NAME || feature.properties.name || "Unknown";\n'
    '                    layer.on({\n'
    '                        mouseover: (e) => e.target.setStyle({ weight: 2, color: "#00ff88", fillOpacity: 0.12 }),\n'
    '                        mouseout: (e) => this.countyLayer.resetStyle(e.target),\n'
    '                        click: () => layer.bindPopup(`<b>${county}</b>`).openPopup()\n'
    '                    });\n'
    '                }\n'
    '            }).addTo(this.map);\n'
    '\n'
    '            this.map.fitBounds(this.countyLayer.getBounds(), { padding: [10, 10] });\n'
    '\n'
    '        } catch (error) {\n'
    '            console.error("[Earthquake] county outline layer failed:", error);\n'
    '        }\n'
    '    },\n'
    '\n'
    '    async loadSatelliteLayer() {',
    "earthquakeengine.js (add loadCountyOutlineLayer method)",
)

print()
print("COUNTY OUTLINE LAYER APPLIED -- hard refresh the browser to pick up the new JS.")
