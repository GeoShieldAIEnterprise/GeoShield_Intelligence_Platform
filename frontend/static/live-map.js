/* GeoShield AI -- Live Map (Sentinel-2 imagery via Main Engine) */
window.GeoShieldLiveMap = {

    map: null,
    satelliteLayer: null,
    streetLayer: null,
    initialized: false,

    init() {
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
    },

    async loadLiveTileLayer() {
        try {
            const res = await fetch("/api/main-engine/tile-layer");
            const data = await res.json();

            const info = document.getElementById("liveMapSceneInfo");

            if (data.mode === "live") {
                this.satelliteLayer = L.tileLayer.wms(data.tile_url_template, {
                    layers: data.wms_layer,
                    format: "image/png",
                    transparent: true,
                    attribution: "Copernicus Sentinel-2 / Sentinel Hub"
                });
                if (info) {
                    info.innerText = `Live Sentinel-2 imagery -- checked ${new Date(data.checked_at).toLocaleString()}`;
                }
            } else {
                this.satelliteLayer = L.tileLayer(data.tile_url_template, {
                    attribution: "Placeholder tiles (Sentinel-2 not authenticated)"
                });
                if (info) {
                    info.innerText = "Sentinel-2 unavailable -- showing placeholder tiles";
                }
            }

            this.satelliteLayer.addTo(this.map);

        } catch (error) {
            console.error("GeoShield Live Map: failed to load tile layer", error);
            const info = document.getElementById("liveMapSceneInfo");
            if (info) info.innerText = "Failed to load Sentinel-2 imagery.";
        }
    },

    switchView(mode) {
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
