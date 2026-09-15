/* GeoShield AI -- Flood Engine (VIIRS live + GPM/ERA5 reference dataset via Main Engine) */
window.GeoShieldFlood = {

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

            this.map = L.map("floodMap", { zoomControl: true }).setView([0.5, 37.5], 6);

            this.streetLayer = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                { attribution: "&copy; OpenStreetMap contributors" }
            );

            this.hotspotLayer = L.layerGroup();

            this.loadSatelliteLayer();
            this.loadCountyFloodLayer();
            this.loadViirsHotspots();
            this.loadSummary();

            const searchInput = document.getElementById("floodSearchInput");
            if (searchInput) {
                searchInput.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") this.searchLocation(searchInput.value);
                });
            }

            document.querySelectorAll('input[name="floodMapView"]').forEach(radio => {
                radio.addEventListener("change", (e) => {
                    this.switchView(e.target.value);
                });
            });

            this.map.invalidateSize();
            console.log("GeoShield Flood Engine initialized (Main Engine connected)");
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
            console.error("[Flood] satellite layer failed:", error);
        }
    },

    async loadCountyFloodLayer() {
        try {
            const [geoRes, countiesRes, gpmRes, era5Res] = await Promise.all([
                fetch("/static/data/kenya_counties.geojson"),
                fetch("/counties"),
                fetch("/api/main-engine/gpm-rainfall"),
                fetch("/api/main-engine/era5-weather")
            ]);
            const data = await geoRes.json();
            const countiesList = await countiesRes.json();
            const gpmData = await gpmRes.json();
            const gpmCounties = gpmData.counties || {};
            const era5Data = await era5Res.json();
            const era5Counties = era5Data.counties || {};

            const countyLookup = {};
            countiesList.forEach(c => { countyLookup[c.County] = c; });
            this.countyLookup = countyLookup;

            const floodRiskLabel = (rainfall) => {
                if (rainfall >= 1200) return "HIGH";
                if (rainfall >= 800) return "MEDIUM";
                return "LOW";
            };

            const flashFloodWatch = (info) => {
                return (Number(info.Temperature_C) >= 32 && Number(info.NDVI) <= 0.35);
            };

            let flashCounties = [];
            countiesList.forEach(c => {
                if (flashFloodWatch(c)) flashCounties.push(c.County);
            });
            const flashEl = document.getElementById("floodFlashWatch");
            if (flashEl) {
                flashEl.innerText = flashCounties.length
                    ? `${flashCounties.length} counties (${flashCounties.slice(0, 5).join(", ")}${flashCounties.length > 5 ? "..." : ""})`
                    : "None currently";
            }

            this.countyLayer = L.geoJSON(data, {
                style: (feature) => {
                    const county = feature.properties.COUNTY || feature.properties.NAME || feature.properties.name || "Unknown";
                    const info = countyLookup[county];
                    const rainfall = info ? Number(info.Rainfall_mm || 0) : 0;
                    let fill = "#a8d8ff";
                    if (rainfall >= 800) fill = "#4a90e2";
                    if (rainfall >= 1200) fill = "#0d47a1";
                    return { color: "#55ffff", weight: 1, fillColor: fill, fillOpacity: 0.5 };
                },
                onEachFeature: (feature, layer) => {
                    const county = feature.properties.COUNTY || feature.properties.NAME || feature.properties.name || "Unknown";

                    layer.on({
                        mouseover: (e) => e.target.setStyle({ weight: 3, color: "#00ff88", fillOpacity: 0.65 }),
                        mouseout: (e) => this.countyLayer.resetStyle(e.target),
                        click: () => {
                            const info = countyLookup[county];
                            if (!info) return;

                            const risk = floodRiskLabel(Number(info.Rainfall_mm));
                            const flash = flashFloodWatch(info) ? "ELEVATED (hot + sparse vegetation)" : "Standard";

                            layer.bindPopup(`
                                <b>${info.County}</b>
                                <hr>
                                🌧️ Rainfall (GPM ref.): ${Number(info.Rainfall_mm).toFixed(0)} mm<br>
                                🌡️ Temperature (ERA5 ref.): ${Number(info.Temperature_C).toFixed(1)} °C<br>
                                🌿 NDVI: ${Number(info.NDVI).toFixed(2)}<br>
                                🌊 Flood Risk: ${risk}<br>
                                ⚡ Flash Flood Watch: ${flash}<br>
                                \ud83c\udf27\ufe0f Today's rainfall (GPM live): ${gpmCounties[county] !== undefined ? gpmCounties[county] + " mm" : "unavailable"}<br>
                                \ud83c\udf21\ufe0f Temperature (ERA5 live): ${era5Counties[county] !== undefined ? era5Counties[county].temperature_c + " \u00b0C" : "unavailable"}
                            `).openPopup();

                            this.map.fitBounds(layer.getBounds(), { padding: [20, 20], maxZoom: 9 });
                        }
                    });
                }
            }).addTo(this.map);

            this.map.fitBounds(this.countyLayer.getBounds(), { padding: [10, 10] });

        } catch (error) {
            console.error("[Flood] county layer failed:", error);
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
                if (frp >= 2) color = "#FF8C00";
                if (frp >= 5) color = "#FF3B30";

                L.circleMarker([parseFloat(h.latitude), parseFloat(h.longitude)], {
                    radius: 5,
                    color: "#8B0000",
                    fillColor: color,
                    fillOpacity: 0.85,
                    weight: 1
                }).bindPopup(`🔥 Active-fire anomaly (VIIRS)<br>FRP: ${h.frp}<br>Detected: ${h.acq_date}`)
                  .addTo(this.hotspotLayer);
            });

            this.hotspotLayer.addTo(this.map);

            const countEl = document.getElementById("floodHotspotCount");
            if (countEl) countEl.innerText = data.count ?? "--";

            const info = document.getElementById("floodSceneInfo");
            if (info) info.innerText = `Flood intelligence -- checked ${new Date(data.checked_at).toLocaleString()}`;

        } catch (error) {
            console.error("[Flood] VIIRS hotspots failed:", error);
        }
    },

    async loadSummary() {
        try {
            const res = await fetch("/summary");
            const data = await res.json();
            const el = document.getElementById("floodHighestRiskCounty");
            if (el && data.highest_rainfall) {
                el.innerText = `${data.highest_rainfall.County} (${Number(data.highest_rainfall.Rainfall_mm).toFixed(0)} mm)`;
            }
        } catch (error) {
            console.error("[Flood] summary failed:", error);
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
            console.error("[Flood] search failed:", error);
        }
    },

    async loadSarLayer() {
        if (this.sarLayer) return;
        try {
            const res = await fetch("/api/main-engine/tile-layer?layer=SAR-FLOOD-VVVH");
            const data = await res.json();

            if (data.mode === "live") {
                this.sarLayer = L.tileLayer.wms(data.tile_url_template, {
                    layers: data.wms_layer,
                    format: "image/png",
                    transparent: true,
                    minZoom: 7,
                    maxZoom: 14,
                    attribution: "Copernicus Sentinel-1 (SAR) / Sentinel Hub"
                });
            }
        } catch (error) {
            console.error("[Flood] SAR layer failed:", error);
        }
    },

    switchView(mode) {
        if (this.satelliteLayer) this.map.removeLayer(this.satelliteLayer);
        if (this.streetLayer) this.map.removeLayer(this.streetLayer);
        if (this.sarLayer) this.map.removeLayer(this.sarLayer);

        if (mode === "street") {
            this.streetLayer.addTo(this.map);
        } else if (mode === "sar") {
            this.loadSarLayer().then(() => {
                if (this.sarLayer) this.sarLayer.addTo(this.map);
            });
        } else {
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