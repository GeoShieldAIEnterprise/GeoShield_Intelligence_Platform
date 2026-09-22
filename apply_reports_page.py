import re

INDEX = "frontend/templates/index.html"
NAV = "frontend/static/workspace-nav.js"

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def must_replace(content, old, new, label):
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"[FAIL] {label}: expected 1 match, found {count}. Aborting without writing.")
    return content.replace(old, new, 1)

# ---------- index.html ----------
html = load(INDEX)

html = must_replace(
    html,
    '<a>\U0001F4C4 Reports</a>',
    '<a id="navReports" style="cursor:pointer;">\U0001F4C4 Reports</a>',
    "sidebar Reports link"
)

reports_section = '''        <section id="geoshieldReportsPage" class="geoshield-workspace-page geoshield-reports-page">
            <div class="livemap-header">
              <div>
                  <h2>\U0001F4C4 GeoShield Reports</h2>
                  <p>Generate downloadable disaster intelligence reports and briefing videos. (Skeleton view -- generation not yet implemented.)</p>
              </div>
              <div class="livemap-controls">
                  <button type="button" id="reportsCloseBtn" class="livemap-close-btn" title="Return to Main Map">&times;</button>
              </div>
            </div>
            <div class="analytics-cards-grid">
              <div class="analytics-card" id="reportsPdfCard">
                  <h3>PDF Report</h3>
                  <div class="analytics-card-body">Coming soon.</div>
              </div>
              <div class="analytics-card" id="reportsVideoCard">
                  <h3>Video Briefing</h3>
                  <div class="analytics-card-body">Coming soon.</div>
              </div>
            </div>
        </section>

'''

html = must_replace(
    html,
    '<section id="geoshieldIntelligencePage" class="geoshield-workspace-page geoshield-intelligence-page">',
    reports_section + '<section id="geoshieldIntelligencePage" class="geoshield-workspace-page geoshield-intelligence-page">',
    "insert Reports HTML section before Intelligence section"
)

html = must_replace(
    html,
    '<script src="/static/earthquakeengine.js"></script>',
    '<script src="/static/earthquakeengine.js"></script>\n<script src="/static/reports.js"></script>',
    "insert reports.js script tag"
)

save(INDEX, html)
print("[OK] index.html patched (3 edits).")

# ---------- workspace-nav.js ----------
nav = load(NAV)

edits = [
    ('    const ALERTS_PAGE = "geoshieldAlertsPage";',
     '    const ALERTS_PAGE = "geoshieldAlertsPage";\n    const REPORTS_PAGE = "geoshieldReportsPage";',
     "add REPORTS_PAGE constant"),

    ('        const alertsPage = document.getElementById(ALERTS_PAGE);',
     '        const alertsPage = document.getElementById(ALERTS_PAGE);\n        const reportsPage = document.getElementById(REPORTS_PAGE);',
     "add reportsPage element lookup"),

    ('            mode === "alerts" ? "alerts" :\n            "map";',
     '            mode === "alerts" ? "alerts" :\n            mode === "reports" ? "reports" :\n            "map";',
     "add reports to mode ternary"),

    ('        const showAlerts = currentWorkspace === "alerts";',
     '        const showAlerts = currentWorkspace === "alerts";\n        const showReports = currentWorkspace === "reports";',
     "add showReports flag"),

    ('        if (alertsPage) {\n            alertsPage.classList.toggle("workspace-page-active", showAlerts);\n        }',
     '        if (alertsPage) {\n            alertsPage.classList.toggle("workspace-page-active", showAlerts);\n        }\n\n        if (reportsPage) {\n            reportsPage.classList.toggle("workspace-page-active", showReports);\n        }',
     "add reportsPage class toggle"),

    ('        document.body.classList.toggle("geoshield-alerts-mode", showAlerts);',
     '        document.body.classList.toggle("geoshield-alerts-mode", showAlerts);\n        document.body.classList.toggle("geoshield-reports-mode", showReports);',
     "add body class toggle for reports mode"),

    ('        if (showAlerts) {\n            if (window.GeoShieldAlerts) {\n                window.GeoShieldAlerts.init();\n                window.GeoShieldAlerts.refreshIfVisible();\n            }\n        }',
     '        if (showAlerts) {\n            if (window.GeoShieldAlerts) {\n                window.GeoShieldAlerts.init();\n                window.GeoShieldAlerts.refreshIfVisible();\n            }\n        }\n\n        if (showReports) {\n            if (window.GeoShieldReports) {\n                window.GeoShieldReports.init();\n                window.GeoShieldReports.refreshIfVisible();\n            }\n        }',
     "add GeoShieldReports init hook"),

    ('    function goToAlerts() {\n        setWorkspace("alerts");\n    }',
     '    function goToAlerts() {\n        setWorkspace("alerts");\n    }\n\n\n    function goToReports() {\n        setWorkspace("reports");\n    }',
     "add goToReports() function"),

    ('        const alertsLink = document.getElementById("navAlerts");\n        if (alertsLink) {\n            alertsLink.addEventListener("click", goToAlerts);\n        }\n\n        const alertsCloseBtn = document.getElementById("alertsCloseBtn");\n        if (alertsCloseBtn) {\n            alertsCloseBtn.addEventListener("click", goToMap);\n        }',
     '        const alertsLink = document.getElementById("navAlerts");\n        if (alertsLink) {\n            alertsLink.addEventListener("click", goToAlerts);\n        }\n\n        const alertsCloseBtn = document.getElementById("alertsCloseBtn");\n        if (alertsCloseBtn) {\n            alertsCloseBtn.addEventListener("click", goToMap);\n        }\n\n        const reportsLink = document.getElementById("navReports");\n        if (reportsLink) {\n            reportsLink.addEventListener("click", goToReports);\n        }\n\n        const reportsCloseBtn = document.getElementById("reportsCloseBtn");\n        if (reportsCloseBtn) {\n            reportsCloseBtn.addEventListener("click", goToMap);\n        }',
     "wire navReports / reportsCloseBtn in initialize()"),

    ('        goToAlerts,\n\n        getCurrentWorkspace: function () {',
     '        goToAlerts,\n        goToReports,\n\n        getCurrentWorkspace: function () {',
     "export goToReports on window.GeoShieldWorkspace"),
]

for old, new, label in edits:
    nav = must_replace(nav, old, new, label)

save(NAV, nav)
print(f"[OK] workspace-nav.js patched ({len(edits)} edits).")

# ---------- new reports.js ----------
reports_js = '''(function () {
    "use strict";

    function init() {
        console.log("GeoShield Reports workspace initialized (skeleton -- generation not yet implemented).");
    }

    function refreshIfVisible() {
        // No live data yet -- placeholder for future PDF/Video generation status.
    }

    window.GeoShieldReports = {
        init,
        refreshIfVisible
    };

})();
'''

save("frontend/static/reports.js", reports_js)
print("[OK] frontend/static/reports.js created.")

print("\\nAll patches applied successfully.")
