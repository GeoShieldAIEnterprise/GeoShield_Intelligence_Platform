from pathlib import Path

# 1. Fully clean and rewrite index.html with clean entities and emoji lock script
html_path = Path("frontend/templates/index.html")
html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GeoShield OS -- Geospatial Intelligence Platform</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/workspace.css">
    <link rel="stylesheet" href="/static/workspace-nav.css">
    <link rel="stylesheet" href="/static/sentinel2.css">
    <link rel="stylesheet" href="/static/live-map.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="/static/emoji-lock.js"></script>
</head>
<body class="geoshield-body">
    <div class="geoshield-shell">
        <header class="geoshield-header">
            <div class="geoshield-brand">
                <h1>GEOSHIELD</h1>
                <span>Geospatial Intelligence Platform</span>
            </div>
            <div class="geoshield-os-title">
                <h2>GeoShield OS</h2>
                <p>Real-Time Disaster Intelligence</p>
            </div>
            <div class="geoshield-header-controls">
                <select id="headerHazardSelect" class="geoshield-select">
                    <option value="fire">&#128293; Fire</option>
                    <option value="drought">&#127760; Drought</option>
                    <option value="flood">&#127754; Flood</option>
                    <option value="earthquake">&#127757; Earthquake</option>
                </select>
                <button id="headerLocateBtn" class="geoshield-btn">&#128205; Locate</button>
                <button id="headerLayersBtn" class="geoshield-btn">&#128391; Layers</button>
                <button id="headerAlertsBtn" class="geoshield-btn">&#128276; Alerts</button>
                <button id="headerSettingsBtn" class="geoshield-btn">&#9881;&#65039; Settings</button>
            </div>
        </header>

        <div class="geoshield-main-layout">
            <nav class="geoshield-sidebar">
                <a href="#dashboard" class="nav-item active" id="navDashboard">&#128202; Dashboard</a>
                <a href="#live-map" class="nav-instance nav-item" id="navLiveMap">&#128640; Live Map</a>
                <a href="#analytics" class="nav-item" id="navAnalytics">&#128200; Analytics</a>
                <a href="#alerts" class="nav-item" id="navAlerts">&#128276; Alerts</a>
                <a href="#reports" class="nav-item" id="navReports">&#128196; Reports</a>
                <div class="sidebar-divider"></div>
                <a href="#flood" class="nav-item" id="navFlood">&#127754; Flood Engine</a>
                <a href="#fire" class="nav-item" id="navFire">&#128293; Fire Engine</a>
                <a href="#earthquake" class="nav-item" id="navEarthquake">&#127757; Earthquake Engine</a>
                <a href="#agriculture" class="nav-item" id="navAgriculture">&#127806; Agriculture</a>
                <div class="sidebar-divider"></div>
                <a href="#settings" class="nav-item" id="navSettings">&#9881;&#65039; Settings</a>
            </nav>

            <main class="geoshield-workspace">
                <!-- Live Map Workspace View -->
                <section id="workspaceLiveMap" class="workspace-view active">
                    <div class="workspace-header">
                        <div id="liveMapTitle" class="workspace-title">&#128640; Live Map -- Sentinel-2 Imagery</div>
                        <div class="workspace-actions">
                            <label><input type="radio" name="liveMapView" value="satellite" checked> Satellite</label>
                            <label><input type="radio" name="liveMapView" value="street"> Street</label>
                        </div>
                    </div>
                    <div id="liveMapSceneInfo" class="scene-info">Initializing satellite stream...</div>
                    <div id="liveMap" class="map-container"></div>
                </section>
                
                <!-- Default Dashboard Workspace View -->
                <section id="workspaceDashboard" class="workspace-view">
                    <div class="workspace-title">&#128202; Command Dashboard</div>
                    <div class="dashboard-grid">
                        <div class="dash-card"><h3>Main Engine Status</h3><p>Operational (Connected to Copernicus)</p></div>
                        <div class="dash-card"><h3>Active Hazards</h3><p>Monitoring 47 Counties</p></div>
                    </div>
                </section>
            </main>
        </div>
    </div>
    <script src="/static/live-map.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>
"""
html_path.write_text(html_content, encoding="utf-8")
print("index.html rewritten with clean UTF-8 encoding.")

# 2. Update live-map.js to handle WMS token properly with Leaflet
live_map_js = Path("frontend/static/live-map.js")
live_map_code = """/* GeoShield AI -- Live Map with Copernicus Sentinel-2 WMS */
window.GeoShieldLiveMap = {
    map: null,
    satelliteLayer: null,
    streetLayer: null,
    initialized: false,
    init() {
        if (this.initialized) {
            this.refreshIfVisible();
            return;
        }
        
        const container = document.getElementById("liveMap");
        if (!container) return;

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
        console.log("GeoShield Live Map initialized.");
    },
    async loadLiveTileLayer() {
        try {
            const res = await fetch("/api/main-engine/tile-layer");
            const data = await res.json();
            const info = document.getElementById("liveMapSceneInfo");
            
            if (data.mode === "live" && data.tile_url_template) {
                // Parse base URL and access token from Main Engine response
                const urlObj = new URL(data.tile_url_template);
                const baseUrl = `${urlObj.origin}${urlObj.pathname}`;
                const accessToken = urlObj.searchParams.get("access_token");

                this.satelliteLayer = L.tileLayer.wms(baseUrl, {
                    layers: data.wms_layer || "TRUE_COLOR",
                    format: "image/png",
                    transparent: true,
                    access_token: accessToken,
                    attribution: "Copernicus Sentinel-2 / Sentinel Hub"
                });
                
                if (info) {
                    info.innerText = `Live Sentinel-2 imagery active -- checked ${new Date(data.checked_at).toLocaleTimeString()}`;
                }
            } else {
                this.satelliteLayer = this.streetLayer;
                if (info) {
                    info.innerText = "Fallback mode: Standard map active.";
                }
            }
            this.satelliteLayer.addTo(this.map);
            this.refreshIfVisible();
        } catch (error) {
            console.error("Failed to load Sentinel-2 layer:", error);
            this.streetLayer.addTo(this.map);
        }
    },
    switchView(mode) {
        if (!this.map) return;
        if (mode === "street") {
            if (this.satelliteLayer && this.map.hasLayer(this.satelliteLayer)) {
                this.map.removeLayer(this.satelliteLayer);
            }
            if (this.streetLayer && !this.map.hasLayer(this.streetLayer)) {
                this.streetLayer.addTo(this.map);
            }
        } else {
            if (this.streetLayer && this.map.hasLayer(this.streetLayer)) {
                this.map.removeLayer(this.streetLayer);
            }
            if (this.satelliteLayer && !this.map.hasLayer(this.satelliteLayer)) {
                this.satelliteLayer.addTo(this.map);
            }
        }
        this.refreshIfVisible();
    },
    refreshIfVisible() {
        if (this.map) {
            setTimeout(() => {
                window.dispatchEvent(new Event("resize"));
                this.map.invalidateSize();
            }, 150);
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    // Navigation toggle bindings for workspaces
    document.querySelectorAll(".geoshield-sidebar .nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
            document.querySelectorAll(".workspace-view").forEach(v => v.classList.remove("active"));
            item.classList.add("active");
            
            const targetId = item.getAttribute("href").replace("#", "workspace");
            // Capitalize camelCase or handle mappings
            const mapIdMap = {
                "workspace-live-map": "workspaceLiveMap",
                "workspacelive-map": "workspaceLiveMap",
                "workspace-dashboard": "workspaceDashboard"
            };
            let matchedView = document.getElementById(targetId) || document.getElementById("workspaceLiveMap");
            if (item.getAttribute("href") === "#live-map") {
                matchedView = document.getElementById("workspaceLiveMap");
                window.GeoShieldLiveMap.init();
            } else if (item.getAttribute("href") === "#dashboard") {
                matchedView = document.getElementById("workspaceDashboard");
            }
            if (matchedView) {
                matchedView.classList.add("active");
                window.GeoShieldLiveMap.refreshIfVisible();
            }
        });
    });
});
"""
live_map_js.write_text(live_map_code, encoding="utf-8")
print("live-map.js updated successfully.")
