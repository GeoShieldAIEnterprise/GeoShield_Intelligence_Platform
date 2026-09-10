from pathlib import Path

# Remove the unauthorized mock dashboard block and restore the exact original workspace layout and template
html_path = Path("frontend/templates/index.html")
original_html = """<!DOCTYPE html>
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
    <div id="app">
        <!-- Original user-defined layout elements -->
        <div class="top-nav">
            <h1>GEOSHIELD</h1>
            <p>Geospatial Intelligence Platform</p>
            <h3>GeoShield OS</h3>
            <p>Real-Time Disaster Intelligence</p>
        </div>
        <div class="workspace-container">
            <div id="liveMap" style="width: 100%; height: 70vh;"></div>
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
html_path.write_text(original_html.strip(), encoding="utf-8")
print("Removed unauthorized dashboard and restored original template.")
