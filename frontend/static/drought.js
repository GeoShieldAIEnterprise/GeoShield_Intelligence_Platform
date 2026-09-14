/* GeoShield AI -- Drought Engine (VIIRS live + GPM/ERA5 reference dataset via Main Engine) */
window.GeoShieldDrought = {

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

            // Centered/zoomed to show all of Kenya, not just Nairobi
            this.map = L.map("droughtMap", { zoomControl: true }).setView([0.5, 37.5], 6);

            this.streetLayer = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                { attribution: "&copy; OpenStreetMap contributors" }
            );

            this.hotspotLayer = L.layerGroup();

            this.loadSatelliteLayer();
            this.loadCountyDroughtLayer();
            this.loadViirsHotspots();
            this.loadSummary();

            const searchInput = document.getElementById("droughtSearchInput");
            if (searchInput) {
                searchInput.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") this.searchLocation(searchInput.value);
                });
            }

            document.querySelectorAll('input[name="droughtMapView"]').forEach(radio => {
                radio.addEventListener("change", (e) => {
                    this.switchView(e.target.value);
                });
            });

            this.map.invalidateSize();
            console.log("GeoShield Drought Engine initialized (Main Engine connected)");
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
            console.error("[Drought] satellite layer failed:", error);
        }
    },

    async loadCountyDroughtLayer() {
        try {
            const [geoRes, countiesRes, gpmRes] = await Promise.all([
                fetch("/static/data/kenya_counties.geojson"),
                fetch("/counties"),
                fetch("/api/main-engine/gpm-rainfall")
            ]);
            const data = await geoRes.json();
            const countiesList = await countiesRes.json();
            const gpmData = await gpmRes.json();
            const gpmCounties = gpmData.counties || {};

            const countyLookup = {};
            countiesList.forEach(c => { countyLookup[c.County] = c; });
            this.countyLookup = countyLookup;

            this.countyLayer = L.geoJSON(data, {
                style: (feature) => {
                    const county = feature.properties.COUNTY || feature.properties.NAME || feature.properties.name || "Unknown";
                    const info = countyLookup[county];
                    const risk = info ? Number(info.Drought_Risk || 0) : 0;
                    let fill = "#00b894";
                    if (risk >= 30) fill = "#f1c40f";
                    if (risk >= 50) fill = "#e67e22";
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

                            layer.bindPopup(`
                                <b>${info.County}</b>
                                <hr>
                                \ud83c\udf27\ufe0f Rainfall (GPM ref.): ${Number(info.Rainfall_mm).toFixed(0)} mm<br>
                                \ud83c\udf21\ufe0f Temperature (ERA5 ref.): ${Number(info.Temperature_C).toFixed(1)} \u00b0C<br>
                                \ud83c\udf3f NDVI: ${Number(info.NDVI).toFixed(2)}<br>
                                \ud83d\udea8 Drought Risk: ${Number(info.Drought_Risk).toFixed(1)}%<br>
                                \ud83c\udf27\ufe0f Today's rainfall (GPM live): ${gpmCounties[county] !== undefined ? gpmCounties[county] + " mm" : "unavailable"}
                            `).openPopup();

                            this.map.fitBounds(layer.getBounds(), { padding: [20, 20], maxZoom: 9 });
                        }
                    });
                }
            }).addTo(this.map);

            this.map.fitBounds(this.countyLayer.getBounds(), { padding: [10, 10] });

        } catch (error) {
            console.error("[Drought] county layer failed:", error);
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
                }).bindPopup(`🔥 Thermal/dryness anomaly (VIIRS)<br>FRP: ${h.frp}<br>Detected: ${h.acq_date}`)
                  .addTo(this.hotspotLayer);
            });

            this.hotspotLayer.addTo(this.map);

            const countEl = document.getElementById("droughtHotspotCount");
            if (countEl) countEl.innerText = data.count ?? "--";

            const info = document.getElementById("droughtSceneInfo");
            if (info) info.innerText = `Drought intelligence -- checked ${new Date(data.checked_at).toLocaleString()}`;

        } catch (error) {
            console.error("[Drought] VIIRS hotspots failed:", error);
        }
    },

    async loadSummary() {
        try {
            const res = await fetch("/summary");
            const data = await res.json();
            const el = document.getElementById("droughtHighestRiskCounty");
            if (el && data.highest_drought) {
                el.innerText = `${data.highest_drought.County} (${Number(data.highest_drought.Drought_Risk).toFixed(1)}%)`;
            }
        } catch (error) {
            console.error("[Drought] summary failed:", error);
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
            console.error("[Drought] search failed:", error);
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




