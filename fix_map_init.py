from pathlib import Path

# Fix map initialization script to explicitly call L.map('liveMap') when the page loads
live_map_js = Path("frontend/static/live-map.js")
live_map_code = """
document.addEventListener("DOMContentLoaded", function() {
    if (typeof L !== 'undefined' && document.getElementById('liveMap')) {
        const map = L.map('liveMap').setView([-1.286389, 36.817222], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        console.log("Leaflet map initialized successfully.");
    }
});
"""
live_map_js.write_text(live_map_code.strip(), encoding="utf-8")
print("Updated live-map.js with explicit Leaflet initialization.")
