from pathlib import Path

html_path = Path("frontend/templates/index.html")
full_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoShield OS -- Geospatial Intelligence Platform</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/workspace-switcher.css">
    <link rel="stylesheet" href="/static/satellite-center.css">
    <link rel="stylesheet" href="/static/sentinel2.css">
    <link rel="stylesheet" href="/static/workspace-nav.css">
    <link rel="stylesheet" href="/static/workspace.css">
    <link rel="stylesheet" href="/static/satellites.css">
    <link rel="stylesheet" href="/static/live-map.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
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
                <a href="#dashboard" class="nav-item" id="navDashboard">&#128202; Dashboard</a>
                <a href="#live-map" class="nav-item active" id="navLiveMap">&#128640; Live Map</a>
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

    <script src="/static/config.js"></script>
    <script src="/static/utils.js"></script>
    <script src="/static/map.js"></script>
    <script src="/static/live-map.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>
"""

html_path.write_text(full_html, encoding="utf-8")
print("Restored complete index.html layout.")
