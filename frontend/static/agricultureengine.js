/* GeoShield AI -- Agriculture Intelligence Engine
   Sentinel-2 NDVI + GPM rainfall + ERA5/Open-Meteo weather
   All live data supplied through the Main Engine / Agriculture API.
*/

window.GeoShieldAgriculture = {

    initialized: false,
    map: null,
    countyLayer: null,
    satelliteLayer: null,
    streetLayer: null,
    records: [],
    recordLookup: {},
    mapMode: "risk",
    baseMode: "street",

    init() {
        if (this.initialized) {
            if (this.map) {
                setTimeout(() => this.map.invalidateSize(), 100);
            }
            this.loadLiveAgriculture();
            return;
        }

        this.initialized = true;

        setTimeout(() => {
            this.initializeMap();
            this.loadLiveAgriculture();
        }, 80);

        console.log("GeoShield Agriculture Engine initialized");
    },

    initializeMap() {
        const mapElement = document.getElementById("agricultureMap");

        if (!mapElement || !window.L) {
            console.error("[Agriculture] Leaflet or agricultureMap element unavailable.");
            return;
        }

        if (this.map) {
            this.map.invalidateSize();
            return;
        }

        this.map = L.map("agricultureMap", {
            zoomControl: true,
            preferCanvas: true
        }).setView([0.5, 37.5], 6);

        this.streetLayer = L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution: "&copy; OpenStreetMap contributors",
                maxZoom: 18
            }
        ).addTo(this.map);

        this.loadSatelliteBase();

        this.map.on("zoomend", () => this.updateSatelliteBanner());

        this.map.invalidateSize();

        console.log("[Agriculture] Leaflet map initialized.");
    },

    async loadSatelliteBase() {
        try {
            const res = await fetch("/api/main-engine/tile-layer");
            if (!res.ok) return;

            const data = await res.json();

            if (data.mode === "live" && data.tile_url_template && data.wms_layer) {
                this.satelliteLayer = L.tileLayer.wms(
                    data.tile_url_template,
                    {
                        layers: data.wms_layer,
                        format: "image/png",
                        transparent: true,
                        minZoom: 7,
                        maxZoom: 16,
                        attribution: "Copernicus Sentinel-2 / Sentinel Hub"
                    }
                );
            } else if (data.tile_url_template) {
                this.satelliteLayer = L.tileLayer(
                    data.tile_url_template,
                    {
                        attribution: "GeoShield satellite imagery"
                    }
                );
            }
        } catch (error) {
            console.warn("[Agriculture] Satellite base unavailable:", error);
        }
    },

    async loadLiveAgriculture() {
        try {
            const res = await fetch("/api/agriculture/live", {
                cache: "no-store"
            });

            if (!res.ok) {
                throw new Error(`Agriculture API returned ${res.status}`);
            }

            const records = await res.json();

            if (!Array.isArray(records)) {
                throw new Error("Agriculture API did not return an array.");
            }

            this.records = records;

            this.recordLookup = {};
            records.forEach(record => {
                this.recordLookup[this.normalizeCounty(record.county)] = record;
            });

            this.updateSummary(records);
            this.updateTable(records);
            this.updateMap(records);

            const info = document.getElementById("agricultureSceneInfo");

            if (info) {
                const liveSources = [
                    records.some(r => r.ndvi_mode === "live") ? "Sentinel-2 NDVI" : null,
                    records.some(r => r.rainfall_mode === "live") ? "GPM-IMERG" : null,
                    records.some(r => r.weather_mode === "live") ? "ERA5/Open-Meteo" : null
                ].filter(Boolean).join(" / ");

                info.innerText =
                    `Live agriculture intelligence -- ${records.length} counties -- ` +
                    `${new Date().toLocaleString()} -- ${liveSources}`;
            }

            if (this.map) {
                setTimeout(() => this.map.invalidateSize(), 100);
            }

        } catch (error) {
            console.error("[Agriculture] live feed failed:", error);

            const info = document.getElementById("agricultureSceneInfo");

            if (info) {
                info.innerText =
                    `Unable to reach agriculture feed -- ${new Date().toLocaleString()}`;
            }
        }
    },

    normalizeCounty(name) {
        return String(name || "")
            .trim()
            .toLowerCase()
            .replace(/\s+/g, " ");
    },

    getCountyName(feature) {
        const properties = feature.properties || {};

        return (
            properties.COUNTY ||
            properties.County ||
            properties.NAME ||
            properties.Name ||
            properties.name ||
            properties.county ||
            "Unknown"
        );
    },

    severityRank(severity) {
        return {
            "Low": 0,
            "Moderate": 1,
            "High": 2,
            "Extreme": 3
        }[severity] ?? 0;
    },

    severityColor(severity) {
        switch (severity) {
            case "Extreme": return "#ff3b30";
            case "High": return "#ff8c00";
            case "Moderate": return "#ffd400";
            default: return "#2ecc71";
        }
    },

    ndviColor(ndvi) {
        const value = Number(ndvi);

        if (!Number.isFinite(value)) return "#64748b";
        if (value < 0.20) return "#b91c1c";
        if (value < 0.30) return "#ef4444";
        if (value < 0.40) return "#f97316";
        if (value < 0.50) return "#eab308";
        if (value < 0.60) return "#84cc16";
        return "#22c55e";
    },

    getMapColor(record) {
        if (!record) return "#475569";

        if (this.mapMode === "ndvi") {
            return this.ndviColor(record.ndvi);
        }

        return this.severityColor(record.severity);
    },

    updateMap(records) {
        if (!this.map || !window.L) return;

        fetch("/static/data/kenya_counties.geojson")
            .then(response => {
                if (!response.ok) {
                    throw new Error(`GeoJSON returned ${response.status}`);
                }
                return response.json();
            })
            .then(geojson => {

                if (this.countyLayer) {
                    this.map.removeLayer(this.countyLayer);
                    this.countyLayer = null;
                }

                this.countyLayer = L.geoJSON(geojson, {

                    style: feature => {
                        const county = this.getCountyName(feature);
                        const record =
                            this.recordLookup[this.normalizeCounty(county)];

                        return {
                            color: "#67e8f9",
                            weight: 1,
                            fillColor: this.getMapColor(record),
                            fillOpacity: 0.62
                        };
                    },

                    onEachFeature: (feature, layer) => {
                        const county = this.getCountyName(feature);
                        const record =
                            this.recordLookup[this.normalizeCounty(county)];

                        layer.on({

                            mouseover: event => {
                                event.target.setStyle({
                                    weight: 3,
                                    color: "#ffffff",
                                    fillOpacity: 0.82
                                });

                                if (event.target.bringToFront) {
                                    event.target.bringToFront();
                                }
                            },

                            mouseout: event => {
                                this.countyLayer.resetStyle(event.target);
                            },

                            click: () => {
                                if (!record) {
                                    layer.bindPopup(
                                        `<b>${county}</b><br>Live agriculture data unavailable.`
                                    ).openPopup();
                                    return;
                                }

                                this.showCountyPopup(layer, record);
                            }
                        });
                    }

                }).addTo(this.map);

                if (this.countyLayer.getBounds().isValid()) {
                    this.map.fitBounds(
                        this.countyLayer.getBounds(),
                        {
                            padding: [20, 20],
                            maxZoom: 7
                        }
                    );
                }

                this.updateLegend();
            })
            .catch(error => {
                console.error("[Agriculture] County GeoJSON failed:", error);
            });
    },

    showCountyPopup(layer, record) {
        const ndvi =
            record.ndvi != null
                ? Number(record.ndvi).toFixed(3)
                : "--";

        const rainfall =
            record.rainfall_mm != null
                ? `${Number(record.rainfall_mm).toFixed(1)} mm`
                : "--";

        const temperature =
            record.temperature_c != null
                ? `${Number(record.temperature_c).toFixed(1)} °C`
                : "--";

        const humidity =
            record.humidity_pct != null
                ? `${Number(record.humidity_pct).toFixed(0)}%`
                : "--";

        const wind =
            record.wind_speed_kmh != null
                ? `${Number(record.wind_speed_kmh).toFixed(1)} km/h`
                : "--";

        const risk =
            record.risk_score != null
                ? `${Number(record.risk_score).toFixed(0)} / 100`
                : "--";

        const riskColor = this.severityColor(record.severity);

        const actions = Array.isArray(record.recommended_actions)
            ? record.recommended_actions
            : [];

        const actionsHtml = actions.length
            ? `<ul style="margin:6px 0 0 18px; padding:0;">
                ${actions.map(action => `<li>${action}</li>`).join("")}
               </ul>`
            : "<span>None listed</span>";

        layer.bindPopup(`
            <div style="min-width:250px;">
                <h3 style="margin:0 0 8px 0;">${record.county}</h3>

                <div><b>🌱 Sentinel-2 NDVI:</b> ${ndvi}</div>
                <div><b>🌧️ Rainfall:</b> ${rainfall}</div>
                <div><b>🌡️ Temperature:</b> ${temperature}</div>
                <div><b>💧 Humidity:</b> ${humidity}</div>
                <div><b>💨 Wind:</b> ${wind}</div>

                <hr style="margin:8px 0;">

                <div>
                    <b>🚨 Agriculture Risk:</b>
                    <span style="color:${riskColor};font-weight:700;">
                        ${record.severity}
                    </span>
                    (${risk})
                </div>

                <div style="margin-top:8px;">
                    <b>Recommended actions:</b>
                    ${actionsHtml}
                </div>

                <hr style="margin:8px 0;">

                <small>
                    NDVI: ${record.ndvi_mode || "--"} |
                    Rainfall: ${record.rainfall_mode || "--"} |
                    Weather: ${record.weather_mode || "--"}
                </small>
            </div>
        `).openPopup();
    },

    updateSummary(records) {
        const countEl = document.getElementById("agricultureCount");
        if (countEl) {
            countEl.innerText = records.length;
        }

        const sorted = [...records].sort(
            (a, b) => this.severityRank(b.severity) - this.severityRank(a.severity)
        );

        const highest = sorted[0];

        const riskEl = document.getElementById("agricultureHighestRisk");

        if (riskEl) {
            riskEl.innerText = highest
                ? `${highest.county} (${highest.severity} - ${highest.risk_score}/100)`
                : "--";
        }

        const overallEl = document.getElementById("agricultureOverallRisk");

        if (overallEl) {
            overallEl.innerText = highest
                ? highest.severity
                : "--";

            if (highest) {
                overallEl.style.color = this.severityColor(highest.severity);
            }
        }

        const ndviEl = document.getElementById("agricultureAverageNdvi");

        if (ndviEl) {
            const values = records
                .map(r => Number(r.ndvi))
                .filter(v => Number.isFinite(v));

            ndviEl.innerText = values.length
                ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(3)
                : "--";
        }
    },

    updateTable(records) {
        const container =
            document.getElementById("agricultureTableContainer");

        if (!container) return;

        const sorted = [...records].sort(
            (a, b) => this.severityRank(b.severity) - this.severityRank(a.severity)
        );

        const rows = sorted.map(record => {

            const riskColor = this.severityColor(record.severity);

            return `
                <tr>
                    <td>${record.county}</td>
                    <td>${record.ndvi != null ? Number(record.ndvi).toFixed(3) : "--"}</td>
                    <td>${record.rainfall_mm != null ? Number(record.rainfall_mm).toFixed(1) + " mm" : "--"}</td>
                    <td>${record.temperature_c != null ? Number(record.temperature_c).toFixed(1) + " °C" : "--"}</td>
                    <td>${record.humidity_pct != null ? Number(record.humidity_pct).toFixed(0) + "%" : "--"}</td>
                    <td>${record.risk_score != null ? Number(record.risk_score).toFixed(0) : "--"}</td>
                    <td style="color:${riskColor};font-weight:700;">
                        ${record.severity || "--"}
                    </td>
                </tr>
            `;
        }).join("");

        container.innerHTML = `
            <div class="agriculture-table-title">
                County Agriculture Intelligence
                <span>${records.length} counties</span>
            </div>

            <div class="agriculture-table-scroll">
                <table class="agriculture-data-table">
                    <thead>
                        <tr>
                            <th>County</th>
                            <th>NDVI</th>
                            <th>Rainfall</th>
                            <th>Temp</th>
                            <th>Humidity</th>
                            <th>Risk Score</th>
                            <th>Severity</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    },

    setMapMode(mode) {
        this.mapMode = mode === "ndvi" ? "ndvi" : "risk";

        if (this.records.length) {
            this.updateMap(this.records);
        }

        this.updateLegend();

        document.querySelectorAll("[data-agriculture-map-mode]")
            .forEach(button => {
                button.classList.toggle(
                    "active",
                    button.dataset.agricultureMapMode === this.mapMode
                );
            });
    },

    updateLegend() {
        const legend = document.getElementById("agricultureMapLegend");

        if (!legend) return;

        if (this.mapMode === "ndvi") {
            legend.innerHTML = `
                <strong>Sentinel-2 NDVI</strong>
                <span><i style="background:#b91c1c"></i> &lt; 0.20</span>
                <span><i style="background:#ef4444"></i> 0.20–0.29</span>
                <span><i style="background:#f97316"></i> 0.30–0.39</span>
                <span><i style="background:#eab308"></i> 0.40–0.49</span>
                <span><i style="background:#84cc16"></i> 0.50–0.59</span>
                <span><i style="background:#22c55e"></i> ≥ 0.60</span>
            `;
        } else {
            legend.innerHTML = `
                <strong>Agriculture Risk</strong>
                <span><i style="background:#2ecc71"></i> Low</span>
                <span><i style="background:#ffd400"></i> Moderate</span>
                <span><i style="background:#ff8c00"></i> High</span>
                <span><i style="background:#ff3b30"></i> Extreme</span>
            `;
        }
    },

    switchBaseMap(mode) {
        if (!this.map) return;

        this.baseMode = mode;

        if (mode === "street") {
            if (this.satelliteLayer && this.map.hasLayer(this.satelliteLayer)) {
                this.map.removeLayer(this.satelliteLayer);
            }
        } else {
            if (this.satelliteLayer && !this.map.hasLayer(this.satelliteLayer)) {
                this.satelliteLayer.addTo(this.map);
            }
        }

        this.updateSatelliteBanner();
    },

    updateSatelliteBanner() {
        const banner = document.getElementById("agricultureSatelliteBanner");
        if (!banner) return;

        const zoom = this.map ? this.map.getZoom() : 0;

        if (this.baseMode !== "street" && zoom < 7) {
            banner.style.display = "block";
        } else {
            banner.style.display = "none";
        }
    },

    refreshIfVisible() {
        if (this.map) {
            setTimeout(() => this.map.invalidateSize(), 100);
        }

        this.loadLiveAgriculture();
    }
};
