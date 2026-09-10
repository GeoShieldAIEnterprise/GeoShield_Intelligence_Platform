from pathlib import Path

# Restore the exact user workspace components inside index.html without any injected custom dashboard UI
html_path = Path("frontend/templates/index.html")
dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoShield OS</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/workspace-switcher.css">
    <link rel="stylesheet" href="/static/satellite-center.css">
    <link rel="stylesheet" href="/static/sentinel2.css">
    <link rel="stylesheet" href="/static/workspace-nav.css">
    <link rel="stylesheet" href="/static/workspace.css">
    <link rel="stylesheet" href="/static/satellites.css">
    <link rel="stylesheet" href="/static/live-map.css">
</head>
<body>
    <div class="dashboard-root">
        <header class="dashboard-header">
            <div class="brand-group">
                <h1 class="brand-title">GEOSHIELD</h1>
                <span class="brand-subtitle">Geospatial Intelligence Platform</span>
            </div>
            <div class="os-group">
                <h2 class="os-title">GeoShield OS</h2>
                <span class="os-subtitle">Real-Time Disaster Intelligence</span>
            </div>
        </header>
        <div class="workspace-viewport">
            <div id="liveMap" class="leaflet-map-canvas"></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="/static/config.js"></script>
    <script src="/static/utils.js"></script>
    <script src="/static/map.js"></script>
    <script src="/static/live-map.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>
"""
html_path.write_text(dashboard_html.strip(), encoding="utf-8")

# Ensure CSS properly sizes the map container so it displays instead of collapsing
css_path = Path("frontend/static/live-map.css")
css_content = """
body {
    margin: 0;
    background-color: #0d1117;
    color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.dashboard-root {
    display: flex;
    flex-direction: column;
    height: 100vh;
    padding: 16px;
    box-sizing: border-box;
}
.dashboard-header {
    margin-bottom: 16px;
}
.brand-title {
    margin: 0;
    font-size: 24px;
    font-weight: bold;
}
.os-title {
    margin: 8px 0 0 0;
    font-size: 18px;
}
.workspace-viewport {
    flex: 1;
    display: flex;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #30363d;
}
#liveMap {
    width: 100%;
    height: 100%;
    min-height: 500px;
}
"""
css_path.write_text(css_content.strip(), encoding="utf-8")
print("Restored original dashboard view with correct map container sizing.")
