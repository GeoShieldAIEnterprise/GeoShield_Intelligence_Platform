from pathlib import Path

path = Path("frontend/static/live-map.js")
src = path.read_text(encoding="utf-8-sig")
original = src

old = '''    init() {
        if (this.initialized) return;
        this.initialized = true; // guard immediately to avoid double-init races

        // Defer map creation slightly so the browser finishes laying out
        // the now-visible container first -- creating a Leaflet map
        // against a still-zero-size element silently results in zero
        // tiles ever being requested.
        setTimeout(() => {
            this.map = L.map("liveMap", { zoomControl: true }).setView([-1.286389, 36.817223], 7);'''

new = '''    init() {
        if (this.initialized) {
            // Already initialized -- just make sure Leaflet recalculates
            // its size in case the container was hidden/shown again,
            // and stop here. Never create a second map instance.
            if (this.map) this.map.invalidateSize();
            return;
        }
        this.initialized = true;

        // Defer map creation slightly so the browser finishes laying out
        // the now-visible container first -- creating a Leaflet map
        // against a still-zero-size element silently results in zero
        // tiles ever being requested.
        setTimeout(() => {
            if (this.map) {
                console.warn("GeoShield Live Map: map already exists, skipping duplicate creation.");
                return;
            }
            this.map = L.map("liveMap", { zoomControl: true }).setView([-1.286389, 36.817223], 7);'''

if old not in src:
    raise SystemExit("ERROR: init() block not found -- printing file:\n" + src)
src = src.replace(old, new)
path.write_text(src, encoding="utf-8", newline="\n")
print("live-map.js patched -- hardened against duplicate map creation.")
