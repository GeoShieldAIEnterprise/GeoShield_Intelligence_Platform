/* GeoShield AI -- Earthquake Engine (USGS live + WorldPop population exposure, via Main Engine) */
window.GeoShieldEarthquake = {

    map: null,
    satelliteLayer: null,
    streetLayer: null,
    countyLayer: null,
    quakeLayer: null,
    initialized: false,

    init() {
        if (this.initialized) {
            if (this.map) this.map.invalidateSize();
            return;
        }
        this.initialized = true;

        setTimeout(() => {
            if (this.map) return;

            this.map = L.map("earthquakeMap", { zoomControl: true }).setView([0.5, 37.5], 6);

            this.streetLayer = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                { attribution: "&copy; OpenStreetMap contributors" }
            );

            this.quakeLayer = L.layerGroup();

            this.loadSatelliteLayer();
            this.loadCountyOutlineLayer();
            this.loadLiveEarthquakes();

            const searchInput = document.getElementById("earthquakeSearchInput");
            if (searchInput) {
                searchInput.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") this.searchLocation(searchInput.value);
                });
            }

            document.querySelectorAll('input[name="earthquakeMapView"]').forEach(radio => {
                radio.addEventListener("change", (e) => {
                    this.switchView(e.target.value);
                });
            });

            this.map.invalidateSize();
            console.log("GeoShield Earthquake Engine initialized (Main Engine connected)");
        }, 50);
    },

    async loadCountyOutlineLayer() {
        try {
            const res = await fetch("/static/data/kenya_counties.geojson");
            const data = await res.json();

            this.countyLayer = L.geoJSON(data, {
                style: () => ({
                    color: "#55ffff",
                    weight: 1,
                    fillColor: "#55ffff",
                    fillOpacity: 0.03
                }),
                onEachFeature: (feature, layer) => {
                    const county = feature.properties.COUNTY || feature.properties.NAME || feature.properties.name || "Unknown";
                    layer.on({
                        mouseover: (e) => e.target.setStyle({ weight: 2, color: "#00ff88", fillOpacity: 0.12 }),
                        mouseout: (e) => this.countyLayer.resetStyle(e.target),
                        click: () => layer.bindPopup(`<b>${county}</b>`).openPopup()
                    });
                }
            }).addTo(this.map);

            this.map.fitBounds(this.countyLayer.getBounds(), { padding: [10, 10] });

        } catch (error) {
            console.error("[Earthquake] county outline layer failed:", error);
        }
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
            console.error("[Earthquake] satellite layer failed:", error);
        }
    },

    severityColor(severity) {
        switch (severity) {
            case "Extreme": return "#FF3B30";
            case "High": return "#FF8C00";
            case "Moderate": return "#FFD400";
            default: return "#2ecc71";
        }
    },

    severityRadius(severity) {
        switch (severity) {
            case "Extreme": return 14;
            case "High": return 11;
            case "Moderate": return 8;
            default: return 6;
        }
    },

    formatPopulation(value) {
        if (value === null || value === undefined) return "unavailable";
        if (value >= 1_000_000) return (value / 1_000_000).toFixed(2) + "M";
        if (value >= 1_000) return (value / 1_000).toFixed(1) + "k";
        return Math.round(value).toString();
    },

    async loadLiveEarthquakes() {
        try {
            const res = await fetch("/api/earthquake/live?period=day&min_magnitude=4.0");
            const events = await res.json();

            this.quakeLayer.clearLayers();

            let highestRisk = null;

            events.forEach(e => {
                const color = this.severityColor(e.severity);
                const radius = this.severityRadius(e.severity);

                if (!highestRisk || e.risk_score > highestRisk.risk_score) {
                    highestRisk = e;
                }

                const actions = (e.recommended_actions || []).map(a => `&bull; ${a}`).join("<br>");
                const populationLine = e.population_mode === "live"
                    ? `${this.formatPopulation(e.population_exposed)} people within 50km (WorldPop, ${e.population_year} model)`
                    : "population data unavailable";

                L.circleMarker([e.latitude, e.longitude], {
                    radius: radius,
                    color: "#8B0000",
                    fillColor: color,
                    fillOpacity: 0.85,
                    weight: 2
                }).bindPopup(`
                    <b>🌍 M${e.magnitude} -- ${e.place || "Unknown location"}</b>
                    <hr>
                    Depth: ${e.depth_km != null ? e.depth_km.toFixed(1) + " km" : "unknown"}<br>
                    County: ${e.county || "Unknown"}<br>
                    Severity: <b>${e.severity}</b> (risk score ${e.risk_score})<br>
                    Population exposed: ${populationLine}<br>
                    <hr>
                    <b>Recommended actions:</b><br>
                    ${actions}
                    <hr>
                    <span style="font-size:11px;color:#94a3b8;">
                        Live feed: USGS Earthquake Hazards Program
                    </span>
                `).addTo(this.quakeLayer);
            });

            this.quakeLayer.addTo(this.map);

            const countEl = document.getElementById("earthquakeCount");
            if (countEl) countEl.innerText = events.length;

            const riskEl = document.getElementById("earthquakeHighestRisk");
            if (riskEl) {
                riskEl.innerText = highestRisk
                    ? `M${highestRisk.magnitude} ${highestRisk.place || ""} (${highestRisk.severity})`
                    : "None (24h)";
            }

            const popEl = document.getElementById("earthquakePopulationNote");
            if (popEl) {
                if (highestRisk) {
                    popEl.innerText = highestRisk.population_mode === "live"
                        ? `${this.formatPopulation(highestRisk.population_exposed)} near highest-risk event (WorldPop ${highestRisk.population_year})`
                        : "Click an event for live reading";
                } else {
                    popEl.innerText = "No active events";
                }
            }

            const info = document.getElementById("earthquakeSceneInfo");
            if (info) info.innerText = `Earthquake intelligence -- checked ${new Date().toLocaleString()} -- source: USGS`;

        } catch (error) {
            console.error("[Earthquake] live feed failed:", error);

            const info = document.getElementById("earthquakeSceneInfo");
            if (info) info.innerText = `Unable to reach earthquake feed -- last attempt ${new Date().toLocaleString()}`;

            const countEl = document.getElementById("earthquakeCount");
            if (countEl) countEl.innerText = "--";

            const riskEl = document.getElementById("earthquakeHighestRisk");
            if (riskEl) riskEl.innerText = "Unavailable";
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
            console.error("[Earthquake] search failed:", error);
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
            this.loadLiveEarthquakes();
        }
    }
};
