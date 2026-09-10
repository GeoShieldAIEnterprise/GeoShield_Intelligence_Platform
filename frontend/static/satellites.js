/* GeoShield OS - Satellite Workspace Controller */
(function () {
    "use strict";

    const DEFAULT_SATELLITES = [
        { id: "sentinel2", name: "Sentinel-2", provider: "Copernicus Data Space", category: "OPTICAL MULTISPECTRAL", description: "Multispectral Earth observation imagery for vegetation, agriculture, fire and environmental intelligence.", status: "active", capabilities: ["True Color", "NDVI", "NDWI", "NBR", "Agriculture", "Fire Analysis", "Change Detection"] },
        { id: "sentinel1", name: "Sentinel-1", provider: "Copernicus Data Space", category: "SAR RADAR", description: "Synthetic Aperture Radar imagery for flood mapping, surface monitoring and all-weather Earth observation.", status: "planned", capabilities: ["Flood Detection", "Surface Monitoring", "Change Detection", "SAR Analysis"] },
        { id: "viirs", name: "VIIRS", provider: "NASA / NOAA", category: "THERMAL / ENVIRONMENTAL", description: "Near-real-time environmental observations for fire, thermal anomalies and atmospheric monitoring.", status: "planned", capabilities: ["Fire Hotspots", "Thermal Anomalies", "Nighttime Lights", "Environmental Monitoring"] },
        { id: "gpm", name: "GPM", provider: "NASA", category: "PRECIPITATION", description: "Global precipitation observations for rainfall monitoring and flood intelligence.", status: "planned", capabilities: ["Rainfall", "Precipitation", "Flood Intelligence"] },
        { id: "era5", name: "ERA5", provider: "ECMWF / Copernicus", category: "CLIMATE / WEATHER", description: "Global atmospheric reanalysis data for weather, climate and environmental intelligence.", status: "planned", capabilities: ["Temperature", "Wind", "Pressure", "Humidity"] }
    ];

    async function loadSatellites() {
        try {
            const res = await fetch("/api/satellites");
            if (!res.ok) throw new Error("API not ready");
            const data = await res.json();
            if (data && Array.isArray(data.satellites) && data.satellites.length > 0) {
                renderSatellites(data.satellites);
                return;
            }
        } catch (err) {
            console.log("Using built-in satellite cards registry.");
        }
        renderSatellites(DEFAULT_SATELLITES);
    }

    function renderSatellites(satellites) {
        const grid = document.getElementById("satelliteGrid");
        const statusEl = document.getElementById("satelliteSystemStatus");
        if (!grid) return;

        const activeCount = satellites.filter(function (s) { return s.status === "active"; }).length;
        if (statusEl) {
            statusEl.textContent = activeCount + " active / " + satellites.length + " registered";
        }

        grid.innerHTML = satellites.map(function (s) {
            const isActive = s.status === "active";
            const badgeText = isActive ? "ACTIVE" : "PLANNED";
            const badgeColor = isActive ? "#059669" : "#475569";
            const q = String.fromCharCode(34);

            const capsHtml = (s.capabilities || []).map(function (c) {
                return "<span style=" + q + "background:#1e293b; color:#94a3b8; font-size:11px; padding:3px 8px; border-radius:4px; margin-right:4px; margin-bottom:4px; display:inline-block;" + q + ">" + c + "</span>";
            }).join("");

            let html = "";
            html += "<div class=" + q + "satellite-card" + q + " data-satellite=" + q + s.id + q + " style=" + q + "background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:20px; min-width:300px;" + q + ">";
            html += "<div style=" + q + "display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;" + q + ">";
            html += "<div><h3 style=" + q + "color:#f8fafc; margin:0 0 4px 0;" + q + ">" + s.name + "</h3>";
            html += "<span style=" + q + "color:#94a3b8; font-size:12px;" + q + ">" + s.provider + "</span></div>";
            html += "<span style=" + q + "background:" + badgeColor + "; color:#fff; font-size:10px; padding:4px 8px; border-radius:4px; font-weight:bold;" + q + ">" + badgeText + "</span>";
            html += "</div>";
            html += "<div style=" + q + "color:#38bdf8; font-size:11px; font-weight:bold; margin-bottom:8px; text-transform:uppercase;" + q + ">" + s.category + "</div>";
            html += "<p style=" + q + "color:#94a3b8; font-size:13px; line-height:1.4; margin-bottom:16px;" + q + ">" + s.description + "</p>";
            html += "<div style=" + q + "margin-bottom:16px;" + q + ">" + capsHtml + "</div>";
            html += isActive ? "<button type=" + q + "button" + q + " class=" + q + "satellite-open-btn" + q + " data-satellite-id=" + q + s.id + q + " style=" + q + "width:100%; padding:10px; background:#2563eb; color:#fff; border:none; border-radius:6px; cursor:pointer; font-weight:600;" + q + ">Open Satellite</button>" : "<button type=" + q + "button" + q + " disabled style=" + q + "width:100%; padding:10px; background:#1e293b; color:#64748b; border:none; border-radius:6px; cursor:not-allowed;" + q + ">Coming Soon</button>";
            html += "</div>";
            return html;
        }).join("");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", loadSatellites);
    } else {
        loadSatellites();
    }
})();
