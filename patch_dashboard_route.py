from pathlib import Path

path = Path("backend/main.py")
src = path.read_text(encoding="utf-8-sig")
original = src

old_import = "from backend.api.satellites import router as satellites_router"
new_import = "from backend.api.satellites import router as satellites_router\nfrom backend.routes.dashboard import router as dashboard_router"

if old_import not in src:
    raise SystemExit("ERROR: satellites import line not found -- printing file:\n" + src)
src = src.replace(old_import, new_import)

old_include = 'app.include_router(satellites_router)'
new_include = 'app.include_router(satellites_router)\napp.include_router(dashboard_router, prefix="/api")'

if old_include not in src:
    raise SystemExit("ERROR: include_router line not found -- printing file:\n" + src)
src = src.replace(old_include, new_include)

if src == original:
    print("No changes were necessary (already patched?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("main.py patched -- real dashboard JSON now served at /api/dashboard, HTML page still at /dashboard.")
