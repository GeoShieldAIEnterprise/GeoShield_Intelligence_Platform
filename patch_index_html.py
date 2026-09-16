from pathlib import Path

path = Path("frontend/templates/index.html")
src = path.read_text(encoding="utf-8-sig")
original = src

# 1. Give the nav link an id + click cursor
nav_anchor = "<a>\U0001f30d Earthquake Engine</a>"
if nav_anchor not in src:
    raise SystemExit("ERROR: earthquake nav link not found -- printing file:\n" + src)
src = src.replace(nav_anchor, '<a id="navEarthquake" style="cursor:pointer;">\U0001f30d Earthquake Engine</a>', 1)

# 2. Add the script include right after fireengine.js
script_anchor = '<script src="/static/fireengine.js"></script>'
if script_anchor not in src:
    raise SystemExit("ERROR: fireengine.js script tag not found -- printing file:\n" + src)
src = src.replace(script_anchor, script_anchor + '\n<script src="/static/earthquakeengine.js"></script>', 1)

# 3. Insert the new earthquake page section right after the Fire page's closing </section>
disclaimer = "VIIRS detects all thermal anomalies, not wildfire specifically"
idx = src.find(disclaimer)
if idx == -1:
    raise SystemExit("ERROR: fire page disclaimer text not found -- printing file:\n" + src)

end_idx = src.find("</section>", idx)
if end_idx == -1:
    raise SystemExit("ERROR: closing </section> after fire page not found -- printing file:\n" + src)
end_idx += len("</section>")

earthquake_section = '''

        <!-- GEOSHIELD EARTHQUAKE ENGINE PAGE -->
        <section id="geoshieldEarthquakePage" class="geoshield-workspace-page geoshield-earthquake-page">
            <div class="livemap-header">
<div>
    <h2>\U0001f30d Earthquake Engine -- USGS / WorldPop</h2>
    <p id="earthquakeSceneInfo">Loading earthquake intelligence...</p>
</div>
<div class="livemap-controls">
    <input type="text" id="earthquakeSearchInput" placeholder="Search a location...">
    <label><input type="radio" name="earthquakeMapView" value="satellite" checked> Satellite</label>
    <label><input type="radio" name="earthquakeMapView" value="street"> Street</label>
    <button type="button" id="earthquakeCloseBtn" class="livemap-close-btn" title="Return to Main Map">\u2715</button>
</div>
            </div>
            <div id="earthquakeMap" class="livemap-container"></div>
            <div id="earthquakeSummaryPanel" class="drought-summary-panel">
<div class="drought-summary-card">
    <span>\U0001f30d Live Earthquakes (past 24h, magnitude 4.0+)</span>
    <strong id="earthquakeCount">--</strong>
</div>
<div class="drought-summary-card">
    <span>\u26a0\ufe0f Highest Risk Event</span>
    <strong id="earthquakeHighestRisk">--</strong>
</div>
<div class="drought-summary-card">
    <span>\U0001f465 Population Exposed (50km radius)</span>
    <strong id="earthquakePopulationNote">Click an event for live reading</strong>
</div>
<div class="drought-summary-card" style="font-size:12px; color:#94a3b8;">
    \U0001f4e1 Live feed: USGS Earthquake Hazards Program (earthquake.usgs.gov). Population exposure: WorldPop Global Project, 2020 modeled population surface, queried live per event.
</div>
            </div>
        </section>'''

src = src[:end_idx] + earthquake_section + src[end_idx:]

if src == original:
    print("No changes were necessary.")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("index.html: patched successfully (nav id, script tag, earthquake page section).")
