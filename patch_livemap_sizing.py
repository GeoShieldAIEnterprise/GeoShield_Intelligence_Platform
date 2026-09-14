from pathlib import Path

path = Path("frontend/static/live-map.js")
src = path.read_text(encoding="utf-8-sig")
original = src

old = '''    init() {
        if (this.initialized) return;

        this.map = L.map("liveMap", { zoomControl: true }).setView([-1.286389, 36.817223], 7);

        this.streetLayer = L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            { attribution: "&copy; OpenStreetMap contributors" }
        );

        this.loadLiveTileLayer();

        document.querySelectorAll('input[name="liveMapView"]').forEach(radio => {
            radio.addEventListener("change", (e) => {
                this.switchView(e.target.value);
            });
        });

        this.initialized = true;
        console.log("GeoShield Live Map initialized (Main Engine connected)");
    },'''

new = '''    init() {
        if (this.initialized) return;
        this.initialized = true; // guard immediately to avoid double-init races

        // Defer map creation slightly so the browser finishes laying out
        // the now-visible container first -- creating a Leaflet map
        // against a still-zero-size element silently results in zero
        // tiles ever being requested.
        setTimeout(() => {
            this.map = L.map("liveMap", { zoomControl: true }).setView([-1.286389, 36.817223], 7);

            this.streetLayer = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                { attribution: "&copy; OpenStreetMap contributors" }
            );

            this.loadLiveTileLayer();

            document.querySelectorAll('input[name="liveMapView"]').forEach(radio => {
                radio.addEventListener("change", (e) => {
                    this.switchView(e.target.value);
                });
            });

            // Force Leaflet to recompute size/tiles now that layout has
            // definitely settled.
            this.map.invalidateSize();

            console.log("GeoShield Live Map initialized (Main Engine connected)");
        }, 50);
    },'''

if old not in src:
    raise SystemExit("ERROR: init() block not found -- printing file:\n" + src)
src = src.replace(old, new)
path.write_text(src, encoding="utf-8", newline="\n")
print("live-map.js patched -- map creation deferred + invalidateSize forced to fix zero-size-container tile bug.")
