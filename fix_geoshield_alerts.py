# -*- coding: utf-8 -*-
"""
fix_geoshield_alerts.py
Applies all Alerts Engine wiring changes to GeoShield in one pass:
  1. Fixes alert_engine.py to aggregate fire severity correctly (worst-per-county)
  2. Adds navAlerts id + Alerts page section + alerts.js script tag to index.html
  3. Wires navAlerts click handling into workspace-nav.js
Run from the project root: python fix_geoshield_alerts.py
"""

import io
import re
import sys

SIREN = "\U0001F6A8"  # the alert emoji, written as an escape to avoid encoding issues

results = []

def report(label, ok):
    results.append((label, ok))
    print(("[OK]   " if ok else "[FAIL] ") + label)


def replace_once(content, old, new, label):
    count = content.count(old)
    if count != 1:
        report(label + " (found %d matches, need exactly 1)" % count, False)
        return content
    content = content.replace(old, new, 1)
    report(label, True)
    return content


# ---------------------------------------------------------------------
# 1. Patch engines/alerts/alert_engine.py
# ---------------------------------------------------------------------
path1 = r"engines\alerts\alert_engine.py"
with io.open(path1, "r", encoding="utf-8") as f:
    content1 = f.read()

pattern = re.compile(
    r'def _get_hazard_severities\(hazard: str\) -> dict\[str, str\]:.*?'
    r'if r\.get\("county"\) and r\.get\("severity"\)\s*\n\s*\}',
    re.DOTALL
)

new_func = '''def _get_hazard_severities(hazard: str) -> dict[str, str]:
    """Read current per-county severity for one hazard via that engine's
    own .analyse() -- this does NOT force a fresh live fetch; each engine
    only recomputes once its own cache window has expired.

    Some hazards (fire) return multiple records per county -- one per
    VIIRS hotspot event, not one per county. A plain dict comprehension
    would keep whichever record happens to be last in the list, which
    can silently under-report severity if a weaker hotspot is enriched
    after a stronger one. Instead we keep the WORST severity seen for
    each county across all its records.
    """
    engine = main_engine.registered_engines.get(hazard)
    if engine is None:
        logger.warning("orchestrator: hazard '%s' not registered on main_engine", hazard)
        return {}
    try:
        records = engine.analyse()
    except Exception:
        logger.exception("orchestrator: %s.analyse() raised", hazard)
        return {}

    worst: dict[str, str] = {}
    for r in records:
        county = r.get("county")
        severity = r.get("severity")
        if not county or not severity:
            continue
        current = worst.get(county)
        if current is None or SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(current, 0):
            worst[county] = severity
    return worst'''

new_content1, n = pattern.subn(new_func, content1, count=1)
if n == 1:
    with io.open(path1, "w", encoding="utf-8") as f:
        f.write(new_content1)
    report("alert_engine.py: fixed fire worst-severity aggregation", True)
else:
    report("alert_engine.py: could not locate function to patch", False)


# ---------------------------------------------------------------------
# 2. Patch frontend/templates/index.html
# ---------------------------------------------------------------------
path2 = r"frontend\templates\index.html"
with io.open(path2, "r", encoding="utf-8") as f:
    content2 = f.read()

# 2a. Give the sidebar link an id
old_link = "<a>" + SIREN + " Alerts</a>"
new_link = '<a id="navAlerts" style="cursor:pointer;">' + SIREN + " Alerts</a>"
content2 = replace_once(content2, old_link, new_link, "index.html: navAlerts sidebar link id")

# 2b. Insert the Alerts page section before the Intelligence page section
alerts_section = (
    "\n        <!-- GEOSHIELD ALERTS PAGE -->\n"
    '        <section id="geoshieldAlertsPage" class="geoshield-workspace-page geoshield-alerts-page">\n'
    '            <div class="livemap-header">\n'
    "                <div>\n"
    "                    <h2>" + SIREN + " GeoShield Alerts</h2>\n"
    "                    <p>New and worsening county-level hazard alerts (Agriculture, Fire, Flood, Drought)</p>\n"
    "                </div>\n"
    '                <div class="livemap-controls">\n'
    '                    <button type="button" id="alertsCloseBtn" class="livemap-close-btn" title="Return to Main Map">&times;</button>\n'
    "                </div>\n"
    "            </div>\n"
    '            <div class="drought-summary-panel">\n'
    '                <div class="drought-summary-card">\n'
    "                    <span>Total alerts</span>\n"
    '                    <strong id="alertsTotalCount">--</strong>\n'
    "                </div>\n"
    "            </div>\n"
    '            <div id="alertsList" style="padding:16px; overflow-y:auto; max-height:70vh;">\n'
    "                Loading alerts...\n"
    "            </div>\n"
    "        </section>\n\n"
)
anchor2 = '        <section id="geoshieldIntelligencePage"'
if content2.count(anchor2) == 1:
    content2 = content2.replace(anchor2, alerts_section + anchor2, 1)
    report("index.html: inserted geoshieldAlertsPage section", True)
else:
    report("index.html: could not find geoshieldIntelligencePage anchor (found %d)" % content2.count(anchor2), False)

# 2c. Add the alerts.js script tag
old_script = '<script src="/static/fireengine.js"></script>'
new_script = old_script + '\n<script src="/static/alerts.js"></script>'
content2 = replace_once(content2, old_script, new_script, "index.html: added alerts.js script tag")

with io.open(path2, "w", encoding="utf-8") as f:
    f.write(content2)


# ---------------------------------------------------------------------
# 3. Patch frontend/static/workspace-nav.js
# ---------------------------------------------------------------------
path3 = r"frontend\static\workspace-nav.js"
with io.open(path3, "r", encoding="utf-8") as f:
    content3 = f.read()

# 3a. Add ALERTS_PAGE const
content3 = replace_once(
    content3,
    '    const ANALYTICS_PAGE = "geoshieldAnalyticsPage";',
    '    const ANALYTICS_PAGE = "geoshieldAnalyticsPage";\n    const ALERTS_PAGE = "geoshieldAlertsPage";',
    "workspace-nav.js: added ALERTS_PAGE const",
)

# 3b. Add alertsPage element lookup
content3 = replace_once(
    content3,
    "        const analyticsPage = document.getElementById(ANALYTICS_PAGE);",
    "        const analyticsPage = document.getElementById(ANALYTICS_PAGE);\n        const alertsPage = document.getElementById(ALERTS_PAGE);",
    "workspace-nav.js: added alertsPage lookup",
)

# 3c. Add to mode-resolution ternary chain
content3 = replace_once(
    content3,
    '            mode === "analytics" ? "analytics" :\n            "map";',
    '            mode === "analytics" ? "analytics" :\n            mode === "alerts" ? "alerts" :\n            "map";',
    "workspace-nav.js: added alerts mode resolution",
)

# 3d. Add showAlerts const
content3 = replace_once(
    content3,
    '        const showAnalytics = currentWorkspace === "analytics";',
    '        const showAnalytics = currentWorkspace === "analytics";\n        const showAlerts = currentWorkspace === "alerts";',
    "workspace-nav.js: added showAlerts const",
)

# 3e. Add alertsPage classList toggle
content3 = replace_once(
    content3,
    '        if (analyticsPage) {\n            analyticsPage.classList.toggle("workspace-page-active", showAnalytics);\n        }',
    '        if (analyticsPage) {\n            analyticsPage.classList.toggle("workspace-page-active", showAnalytics);\n        }\n\n        if (alertsPage) {\n            alertsPage.classList.toggle("workspace-page-active", showAlerts);\n        }',
    "workspace-nav.js: added alertsPage classList toggle",
)

# 3f. Add body class toggle
content3 = replace_once(
    content3,
    '        document.body.classList.toggle("geoshield-analytics-mode", showAnalytics);',
    '        document.body.classList.toggle("geoshield-analytics-mode", showAnalytics);\n        document.body.classList.toggle("geoshield-alerts-mode", showAlerts);',
    "workspace-nav.js: added body class toggle",
)

# 3g. Add showAlerts init block
content3 = replace_once(
    content3,
    '        if (showAnalytics) {\n            if (window.GeoShieldAnalytics) {\n                window.GeoShieldAnalytics.init();\n                window.GeoShieldAnalytics.refreshIfVisible();\n            }\n        }',
    '        if (showAnalytics) {\n            if (window.GeoShieldAnalytics) {\n                window.GeoShieldAnalytics.init();\n                window.GeoShieldAnalytics.refreshIfVisible();\n            }\n        }\n\n        if (showAlerts) {\n            if (window.GeoShieldAlerts) {\n                window.GeoShieldAlerts.init();\n                window.GeoShieldAlerts.refreshIfVisible();\n            }\n        }',
    "workspace-nav.js: added showAlerts init call",
)

# 3h. Add goToAlerts function
content3 = replace_once(
    content3,
    '    function goToAnalytics() {\n        setWorkspace("analytics");\n    }',
    '    function goToAnalytics() {\n        setWorkspace("analytics");\n    }\n\n\n    function goToAlerts() {\n        setWorkspace("alerts");\n    }',
    "workspace-nav.js: added goToAlerts function",
)

# 3i. Wire up the link + close button in initialize()
content3 = replace_once(
    content3,
    '        const analyticsLink = document.getElementById("navAnalytics");\n        if (analyticsLink) {\n            analyticsLink.addEventListener("click", goToAnalytics);\n        }\n\n        const analyticsCloseBtn = document.getElementById("analyticsCloseBtn");\n        if (analyticsCloseBtn) {\n            analyticsCloseBtn.addEventListener("click", goToMap);\n        }',
    '        const analyticsLink = document.getElementById("navAnalytics");\n        if (analyticsLink) {\n            analyticsLink.addEventListener("click", goToAnalytics);\n        }\n\n        const analyticsCloseBtn = document.getElementById("analyticsCloseBtn");\n        if (analyticsCloseBtn) {\n            analyticsCloseBtn.addEventListener("click", goToMap);\n        }\n\n        const alertsLink = document.getElementById("navAlerts");\n        if (alertsLink) {\n            alertsLink.addEventListener("click", goToAlerts);\n        }\n\n        const alertsCloseBtn = document.getElementById("alertsCloseBtn");\n        if (alertsCloseBtn) {\n            alertsCloseBtn.addEventListener("click", goToMap);\n        }',
    "workspace-nav.js: wired navAlerts link + close button",
)

# 3j. Export goToAlerts
content3 = replace_once(
    content3,
    "        goToAgriculture,\n        goToAnalytics,\n\n        getCurrentWorkspace: function () {",
    "        goToAgriculture,\n        goToAnalytics,\n        goToAlerts,\n\n        getCurrentWorkspace: function () {",
    "workspace-nav.js: exported goToAlerts",
)

with io.open(path3, "w", encoding="utf-8") as f:
    f.write(content3)


# ---------------------------------------------------------------------
print("\n---- SUMMARY ----")
failed = [label for label, ok in results if not ok]
if failed:
    print("%d step(s) FAILED -- files were still saved with whatever succeeded." % len(failed))
    for label in failed:
        print("  - " + label)
    sys.exit(1)
else:
    print("All %d steps applied successfully." % len(results))
