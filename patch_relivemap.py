from pathlib import Path

path = Path("frontend/templates/index.html")
src = path.read_text(encoding="utf-8-sig")
original = src

anchor = '        <section id="geoshieldIntelligencePage" class="geoshield-workspace-page geoshield-intelligence-page">'

if anchor not in src:
    raise SystemExit("ERROR: anchor not found -- printing surrounding context:\n" + src[:200])

livemap_section = '''        <!-- GEOSHIELD LIVE MAP PAGE (Sentinel-2 imagery) -->
        <section id="geoshieldLiveMapPage" class="geoshield-workspace-page geoshield-livemap-page">
            <div class="livemap-header">
                <div>
                    <h2>\U0001F6F0\uFE0F Live Map -- Sentinel-2 Imagery</h2>
                    <p id="liveMapSceneInfo">Loading latest scene...</p>
                </div>
                <div class="livemap-controls">
                    <label><input type="radio" name="liveMapView" value="satellite" checked> Satellite</label>
                    <label><input type="radio" name="liveMapView" value="street"> Street</label>
                    <button type="button" id="liveMapCloseBtn" class="livemap-close-btn" title="Return to Main Map">\u2715</button>
                </div>
            </div>
            <div id="liveMap" class="livemap-container"></div>
        </section>

'''

src = src.replace(anchor, livemap_section + anchor, 1)

# Re-add the live-map.js script include if it's missing too
if '/static/live-map.js' not in src:
    old_script = '<script src="/static/workspace-nav.js"></script>'
    new_script = '<script src="/static/live-map.js"></script>\n<script src="/static/workspace-nav.js"></script>'
    if old_script not in src:
        raise SystemExit("ERROR: workspace-nav.js script tag not found -- printing tail of file:\n" + src[-1500:])
    src = src.replace(old_script, new_script, 1)

if src == original:
    print("No changes were necessary (already present?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("index.html patched -- Live Map page section and script include restored.")
