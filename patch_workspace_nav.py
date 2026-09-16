from pathlib import Path

def patch(path_str, anchor, addition, label):
    path = Path(path_str)
    src = path.read_text(encoding="utf-8-sig")
    original = src
    if anchor not in src:
        raise SystemExit(f"ERROR: anchor not found for {label} -- printing file:\n" + src)
    src = src.replace(anchor, addition, 1)
    if src == original:
        print(f"{label}: no changes were necessary.")
    else:
        path.write_text(src, encoding="utf-8", newline="\n")
        print(f"{label}: patched successfully.")

FILE = "frontend/static/workspace-nav.js"

patch(FILE,
    '    const FIRE_PAGE = "geoshieldFirePage";',
    '    const FIRE_PAGE = "geoshieldFirePage";\n    const EARTHQUAKE_PAGE = "geoshieldEarthquakePage";',
    "consts")

patch(FILE,
    '        const firePage = document.getElementById(FIRE_PAGE);',
    '        const firePage = document.getElementById(FIRE_PAGE);\n        const earthquakePage = document.getElementById(EARTHQUAKE_PAGE);',
    "getElementById")

patch(FILE,
    '            mode === "fire" ? "fire" :\n            "map";',
    '            mode === "fire" ? "fire" :\n            mode === "earthquake" ? "earthquake" :\n            "map";',
    "ternary")

patch(FILE,
    '        const showFire = currentWorkspace === "fire";',
    '        const showFire = currentWorkspace === "fire";\n        const showEarthquake = currentWorkspace === "earthquake";',
    "showFire const")

patch(FILE,
    '        if (firePage) {\n            firePage.classList.toggle("workspace-page-active", showFire);\n        }',
    '        if (firePage) {\n            firePage.classList.toggle("workspace-page-active", showFire);\n        }\n\n        if (earthquakePage) {\n            earthquakePage.classList.toggle("workspace-page-active", showEarthquake);\n        }',
    "page toggle")

patch(FILE,
    '        document.body.classList.toggle("geoshield-fire-mode", showFire);',
    '        document.body.classList.toggle("geoshield-fire-mode", showFire);\n        document.body.classList.toggle("geoshield-earthquake-mode", showEarthquake);',
    "body class toggle")

patch(FILE,
    '        if (showFire) {\n            if (window.GeoShieldFire) {\n                window.GeoShieldFire.init();\n                window.GeoShieldFire.refreshIfVisible();\n            }\n        }',
    '        if (showFire) {\n            if (window.GeoShieldFire) {\n                window.GeoShieldFire.init();\n                window.GeoShieldFire.refreshIfVisible();\n            }\n        }\n\n        if (showEarthquake) {\n            if (window.GeoShieldEarthquake) {\n                window.GeoShieldEarthquake.init();\n                window.GeoShieldEarthquake.refreshIfVisible();\n            }\n        }',
    "init call")

patch(FILE,
    '    function goToFire() {\n        setWorkspace("fire");\n    }',
    '    function goToFire() {\n        setWorkspace("fire");\n    }\n\n\n    function goToEarthquake() {\n        setWorkspace("earthquake");\n    }',
    "goTo function")

patch(FILE,
    '        const fireLink = document.getElementById("navFire");\n        if (fireLink) {\n            fireLink.addEventListener("click", goToFire);\n        }\n\n        const fireCloseBtn = document.getElementById("fireCloseBtn");\n        if (fireCloseBtn) {\n            fireCloseBtn.addEventListener("click",goToMap);\n        }',
    '        const fireLink = document.getElementById("navFire");\n        if (fireLink) {\n            fireLink.addEventListener("click", goToFire);\n        }\n\n        const fireCloseBtn = document.getElementById("fireCloseBtn");\n        if (fireCloseBtn) {\n            fireCloseBtn.addEventListener("click",goToMap);\n        }\n\n        const earthquakeLink = document.getElementById("navEarthquake");\n        if (earthquakeLink) {\n            earthquakeLink.addEventListener("click", goToEarthquake);\n        }\n\n        const earthquakeCloseBtn = document.getElementById("earthquakeCloseBtn");\n        if (earthquakeCloseBtn) {\n            earthquakeCloseBtn.addEventListener("click", goToMap);\n        }',
    "initialize bindings")

patch(FILE,
    '        goToFlood,\n        goToFire,',
    '        goToFlood,\n        goToFire,\n        goToEarthquake,',
    "export object")

print()
print("workspace-nav.js: ALL PATCHES APPLIED SUCCESSFULLY.")
