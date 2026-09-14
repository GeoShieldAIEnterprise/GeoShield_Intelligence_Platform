from pathlib import Path

path = Path("frontend/static/live-map.js")
src = path.read_text(encoding="utf-8-sig")
original = src

old = '''                this.satelliteLayer = L.tileLayer.wms(data.tile_url_template, {
                    layers: data.wms_layer,
                    format: "image/png",
                    transparent: true,
                    version: "1.3.0",
                    crs: L.CRS.EPSG3857,
                    attribution: "Copernicus Sentinel-2 / Sentinel Hub"
                });

                this.satelliteLayer.on("tileerror", function (error) {
                    console.error("GeoShield Live Map: WMS tile failed to load:", error);
                });'''

new = '''                this.satelliteLayer = L.tileLayer.wms(data.tile_url_template, {
                    layers: data.wms_layer,
                    format: "image/png",
                    transparent: true,
                    version: "1.3.0",
                    crs: L.CRS.EPSG3857,
                    minZoom: 5,
                    maxZoom: 16,
                    attribution: "Copernicus Sentinel-2 / Sentinel Hub"
                });

                this.satelliteLayer.on("tileerror", function (error) {
                    console.error("GeoShield Live Map: WMS tile failed to load. Tile coords:", error.coords, "Error:", error.error);
                });

                this.map.setMinZoom(5);
                this.map.setMaxZoom(16);'''

if old not in src:
    raise SystemExit("ERROR: WMS layer block not found -- printing file:\n" + src)
src = src.replace(old, new)
path.write_text(src, encoding="utf-8", newline="\n")
print("live-map.js patched -- added zoom bounds matching typical Sentinel Hub serving range, and richer tileerror logging.")
