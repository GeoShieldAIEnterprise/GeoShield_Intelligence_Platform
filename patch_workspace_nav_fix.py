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

# 1. Add earthquake link/close button bindings, right before the READY log line
patch(FILE,
    '        const fireCloseBtn = document.getElementById("fireCloseBtn");\n'
    '        if (fireCloseBtn) {\n'
    '            fireCloseBtn.addEventListener("click", goToMap);\n'
    '        }\n'
    '\n'
    '        console.log("GeoShield Workspace Navigation READY");',

    '        const fireCloseBtn = document.getElementById("fireCloseBtn");\n'
    '        if (fireCloseBtn) {\n'
    '            fireCloseBtn.addEventListener("click", goToMap);\n'
    '        }\n'
    '\n'
    '        const earthquakeLink = document.getElementById("navEarthquake");\n'
    '        if (earthquakeLink) {\n'
    '            earthquakeLink.addEventListener("click", goToEarthquake);\n'
    '        }\n'
    '\n'
    '        const earthquakeCloseBtn = document.getElementById("earthquakeCloseBtn");\n'
    '        if (earthquakeCloseBtn) {\n'
    '            earthquakeCloseBtn.addEventListener("click", goToMap);\n'
    '        }\n'
    '\n'
    '        console.log("GeoShield Workspace Navigation READY");',
    "initialize bindings (fixed anchor)")

# 2. Add goToEarthquake to the exported object
patch(FILE,
    '        goToFlood,\n'
    '        goToFire,\n'
    '\n'
    '        getCurrentWorkspace: function () {',

    '        goToFlood,\n'
    '        goToFire,\n'
    '        goToEarthquake,\n'
    '\n'
    '        getCurrentWorkspace: function () {',
    "export object (fixed anchor)")

print()
print("workspace-nav.js: remaining patches applied successfully.")
