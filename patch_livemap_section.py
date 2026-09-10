from pathlib import Path

path = Path("frontend/templates/index.html")
src = path.read_text(encoding="utf-8-sig")
original = src

# Insert a new Live Map page section right after the main map page closes
anchor = '''        </section>

        <!-- GEOSHIELD SATELLITE INTELLIGENCE PAGE -->'''

new_section = '''        </section>

        <!-- GEOSHIELD LIVE MAP PAGE (Sentinel-2 imagery) -->
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

        <!-- GEOSHIELD SATELLITE INTELLIGENCE PAGE -->'''

if anchor not in src:
    raise SystemExit("ERROR: anchor not found -- printing file:\n" + src)
src = src.replace(anchor, new_section, 1)

if src == original:
    print("No changes were necessary (already patched?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("index.html patched -- Live Map page section added.")
