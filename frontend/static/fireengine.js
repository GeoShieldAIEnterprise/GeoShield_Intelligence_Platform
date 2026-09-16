/* GeoShield AI -- Fire Engine (VIIRS live primary + ERA5/GPM live context via Main Engine) */
window.GeoShieldFire = {

    map: null,
    satelliteLayer: null,
    streetLayer: null,
    countyLayer: null,
    hotspotLayer: null,
    initialized: false,

    init() {
        if (this.initialized) {
            if (this.map) this.map.invalidateSize();
            return;
        }
        this.initialized = true;

        setTimeout(() => {
            if (this.map) return;

            this.map = L.map("fireMap", { zoomControl: true }).setView([0.5, 37.5], 6);

            this.streetLayer = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                { attribution: "&copy; OpenStreetMap contributors" }
            );

            this.hotspotLayer = L.layerGroup();

            this.loadSatelliteLayer();
            this.loadCountyFireLayer();
            this.loadViirsHotspots();
            this.loadSummary();

            const searchInput = document.getElementById("fireSearchInput");
            if (searchInput) {
                searchInput.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") this.searchLocation(searchInput.value);
                });
            }

            document.querySelectorAll('input[name="fireMapView"]').forEach(radio => {
                radio.addEventListener("change", (e) => {
                    this.switchView(e.target.value);
                });
            });

            this.map.invalidateSize();
            console.log("GeoShield Fire Engine initialized (Main Engine connected)");
        }, 50);
    },

    async loadSatelliteLayer() {
        try {
            const res = await fetch("/api/main-engine/tile-layer");
            const data = await res.json();

            if (data.mode === "live") {
                this.satelliteLayer = L.tileLayer.wms(data.tile_url_template, {
                    layers: data.wms_layer,
                    format: "image/png",
                    transparent: true,
                    minZoom: 7,
                    maxZoom: 14,
                    attribution: "Copernicus Sentinel-2 / Sentinel Hub"
                });
            } else {
                this.satelliteLayer = L.tileLayer(data.tile_url_template, {
                    attribution: "Placeholder tiles (Sentinel-2 not authenticated)"
                });
            }

            this.satelliteLayer.addTo(this.map);
        } catch (error) {
            console.error("[Fire] satellite layer failed:", error);
        }
    },

    async loadCountyFireLayer() {
        try {
            const [geoRes, countiesRes, era5Res] = await Promise.all([
                fetch("/static/data/kenya_counties.geojson"),
                fetch("/counties"),
                fetch("/api/main-engine/era5-weather")
            ]);
            const data = await geoRes.json();
            const countiesList = await countiesRes.json();
            const era5Data = await era5Res.json();
            const era5Counties = era5Data.counties || {};

            const countyLookup = {};
            countiesList.forEach(c => { countyLookup[c.County] = c; });
            this.countyLookup = countyLookup;

            const fireRiskLabel = (droughtRisk) => {
                if (droughtRisk >= 70) return "HIGH";
                if (droughtRisk >= 40) return "MEDIUM";
                return "LOW";
            };

            this.countyLayer = L.geoJSON(data, {
                style: (feature) => {
                    const county = feature.properties.COUNTY || feature.properties.NAME || feature.properties.name || "Unknown";
                    const info = countyLookup[county];
                    const risk = info ? Number(info.Drought_Risk || 0) : 0;
                    let fill = "#2ecc71";
                    if (risk >= 40) fill = "#f1c40f";
                    if (risk >= 70) fill = "#e74c3c";
                    return { color: "#55ffff", weight: 1, fillColor: fill, fillOpacity: 0.4 };
                },
                onEachFeature: (feature, layer) => {
                    const county = feature.properties.COUNTY || feature.properties.NAME || feature.properties.name || "Unknown";

                    layer.on({
                        mouseover: (e) => e.target.setStyle({ weight: 3, color: "#00ff88", fillOpacity: 0.55 }),
                        mouseout: (e) => this.countyLayer.resetStyle(e.target),
                        click: () => {
                            const info = countyLookup[county];
                            if (!info) return;

                            const risk = fireRiskLabel(Number(info.Drought_Risk));
                            const era5 = era5Counties[county];
                            const tempLine = era5 ? `${era5.temperature_c} \u00b0C (live)` : "unavailable";

                            layer.bindPopup(`
                                <b>${info.County}</b>
                                <hr>
                                \ud83c\udf3f NDVI (vegetation dryness): ${Number(info.NDVI).toFixed(2)}<br>
                                \ud83d\udd25 Fire Risk: ${risk}<br>
                                \ud83c\udf21\ufe0f Temperature (ERA5 live): ${tempLine}
                            `).openPopup();

                            const tempNote = document.getElementById("fireTempNote");
                            if (tempNote) tempNote.innerText = `${county}: ${tempLine}`;

                            this.map.fitBounds(layer.getBounds(), { padding: [20, 20], maxZoom: 9 });
                        }
                    });
                }
            }).addTo(this.map);

            this.map.fitBounds(this.countyLayer.getBounds(), { padding: [10, 10] });

        } catch (error) {
            console.error("[Fire] county layer failed:", error);
        }
    },

    async loadViirsHotspots() {
        try {
            const res = await fetch("/api/main-engine/viirs-hotspots");
            const data = await res.json();

            this.hotspotLayer.clearLayers();

            (data.hotspots || []).forEach(h => {
                const frp = parseFloat(h.frp) || 0;
                let color = "#FFD400";
                let radius = 6;
                if (frp >= 2) { color = "#FF8C00"; radius = 8; }
                if (frp >= 5) { color = "#FF3B30"; radius = 11; }

                L.circleMarker([parseFloat(h.latitude), parseFloat(h.longitude)], {
                    radius: radius,
                    color: "#8B0000",
                    fillColor: color,
                    fillOpacity: 0.9,
                    weight: 2
                }).bindPopup(`\ud83d\udd25 Active fire (VIIRS)<br>FRP: ${h.frp}<br>Brightness: ${h.bright_ti4}<br>Detected: ${h.acq_date}`)
                  .addTo(this.hotspotLayer);
            });

            this.hotspotLayer.addTo(this.map);

            const countEl = document.getElementById("fireHotspotCount");
            if (countEl) countEl.innerText = data.count ?? "--";

            const info = document.getElementById("fireSceneInfo");
            if (info) info.innerText = `Fire intelligence -- checked ${new Date(data.checked_at).toLocaleString()}`;

        } catch (error) {
            console.error("[Fire] VIIRS hotspots failed:", error);
        }
    },

    async loadSummary() {
        try {
            const res = await fetch("/summary");
            const data = await res.json();
            const el = document.getElementById("fireHighestRiskCounty");
            if (el && data.highest_drought) {
                el.innerText = `${data.highest_drought.County} (${Number(data.highest_drought.Drought_Risk).toFixed(1)}% dryness)`;
            }
        } catch (error) {
            console.error("[Fire] summary failed:", error);
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
            this.map.setView([parseFloat(lat), parseFloat(lon)], 10);
        } catch (error) {
            console.error("[Fire] search failed:", error);
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
