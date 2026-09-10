from pathlib import Path

html_path = Path("frontend/templates/index.html")
code = html_path.read_text(encoding="utf-8")

# Reconstruct a clean, properly structured HTML template with standard CSS layout wrappers
new_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoShield OS - Real-Time Disaster Intelligence</title>
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
    <div class="geoshield-app-layout">
        <header class="app-header">
            <div class="brand-title">GEOSHIELD</div>
            <div class="brand-subtitle">Geospatial Intelligence Platform</div>
            <div class="os-title">GeoShield OS</div>
            <div class="os-subtitle">Real-Time Disaster Intelligence</div>
        </header>
        
        <div class="workspace-nav-bar">
            <!-- Controls and Nav -->
        </div>

        <main class="workspace-viewport">
            <div id="liveMap" style="width: 100%; height: 75vh;"></div>
        </main>
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
html_path.write_text(new_html.strip(), encoding="utf-8")
print("Rebuilt index.html with clean layout wrappers.")
