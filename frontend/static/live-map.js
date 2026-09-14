/* GeoShield AI -- Live Map (Sentinel-2 imagery via Main Engine) */
window.GeoShieldLiveMap = {

    map: null,
    satelliteLayer: null,
    streetLayer: null,
    initialized: false,

    init() {
        if (this.initialized) {
            if (this.map) this.map.invalidateSize();
            return;
        }
        this.initialized = true;

        setTimeout(() => {
            if (this.map) {
                console.warn("GeoShield Live Map: map already exists, skipping duplicate creation.");
                return;
            }
            this.map = L.map("liveMap", { zoomControl: true }).setView([-1.286389, 36.817223], 7);

            this.streetLayer = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                { attribution: "&copy; OpenStreetMap contributors" }
            );

            console.log("[LiveMap TRACE] map created, calling loadLiveTileLayer()");
            this.loadLiveTileLayer();

            const searchBtn = document.getElementById("liveMapSearchBtn");
            const searchInput = document.getElementById("liveMapSearchInput");
            if (searchBtn && searchInput) {
                searchBtn.addEventListener("click", () => this.searchLocation(searchInput.value));
                searchInput.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") this.searchLocation(searchInput.value);
                });
            }

            document.querySelectorAll('input[name="liveMapView"]').forEach(radio => {
                radio.addEventListener("change", (e) => {
                    this.switchView(e.target.value);
                });
            });

            this.map.invalidateSize();
            console.log("GeoShield Live Map initialized (Main Engine connected)");
        }, 50);
    },

    async loadLiveTileLayer() {
        console.log("[LiveMap TRACE] loadLiveTileLayer() started");
        try {
            console.log("[LiveMap TRACE] fetching /api/main-engine/tile-layer ...");
            const res = await fetch("/api/main-engine/tile-layer");
            console.log("[LiveMap TRACE] fetch responded, status:", res.status);

            const data = await res.json();
            console.log("[LiveMap TRACE] JSON parsed, mode:", data.mode, "full data:", data);

            const info = document.getElementById("liveMapSceneInfo");
            console.log("[LiveMap TRACE] info element found?", !!info);

            if (data.mode === "live") {
                console.log("[LiveMap TRACE] constructing WMS layer...");
                this.satelliteLayer = L.tileLayer.wms(data.tile_url_template, {
                    layers: data.wms_layer,
                    format: "image/png",
                    transparent: true,
                    minZoom: 7,
                    maxZoom: 14,
                    attribution: "Copernicus Sentinel-2 / Sentinel Hub"
                });
                console.log("[LiveMap TRACE] WMS layer object created:", this.satelliteLayer);

                this.satelliteLayer.on("tileerror", function (error) {
                    console.error("[LiveMap TRACE] tileerror event:", error);
                });

                if (info) {
                    info.innerText = `Live Sentinel-2 imagery -- checked ${new Date(data.checked_at).toLocaleString()}`;
                    console.log("[LiveMap TRACE] info text updated");
                }
            } else {
                console.log("[LiveMap TRACE] mode was NOT live, using placeholder tiles");
                this.satelliteLayer = L.tileLayer(data.tile_url_template, {
                    attribution: "Placeholder tiles (Sentinel-2 not authenticated)"
                });
                if (info) {
                    info.innerText = "Sentinel-2 unavailable -- showing placeholder tiles";
                }
            }

            console.log("[LiveMap TRACE] calling addTo(map), map exists?", !!this.map);
            this.satelliteLayer.addTo(this.map);
            console.log("[LiveMap TRACE] addTo() completed successfully");

        } catch (error) {
            console.error("[LiveMap TRACE] CAUGHT ERROR:", error, error.stack);
            const info = document.getElementById("liveMapSceneInfo");
            if (info) info.innerText = "Failed to load Sentinel-2 imagery.";
        }
    },

    async searchLocation(query) {
        if (!query || !query.trim()) return;
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`);
            const results = await res.json();
            if (!results.length) {
                alert("Location not found: " + query);
                return;
            }
            const { lat, lon } = results[0];
            this.map.setView([parseFloat(lat), parseFloat(lon)], 14);
        } catch (error) {
            console.error("[LiveMap] search failed:", error);
            alert("Search failed. Check your connection.");
        }
    },

    switchView(mode) {
        console.log("[LiveMap TRACE] switchView before:", mode, this.map.getCenter(), this.map.getZoom());
        if (mode === "street") {
            if (this.satelliteLayer) this.map.removeLayer(this.satelliteLayer);
            this.streetLayer.addTo(this.map);
        } else {
            if (this.streetLayer) this.map.removeLayer(this.streetLayer);
            if (this.satelliteLayer) this.satelliteLayer.addTo(this.map);
        }
    },

    refreshIfVisible() {
        if (this.map) {
            window.dispatchEvent(new Event("resize"));
            this.map.invalidateSize();
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    console.log("Live Map module loaded.");
});







