from pathlib import Path

path = Path("backend/main.py")
src = path.read_text(encoding="utf-8-sig")
original = src

old_import = "from backend.routes.dashboard import router as dashboard_router"
new_import = "from backend.routes.dashboard import router as dashboard_router\nfrom backend.api.sentinel2_map_layer import router as sentinel2_map_layer_router"
if old_import not in src:
    raise SystemExit("ERROR: dashboard import line not found -- printing file:\n" + src)
src = src.replace(old_import, new_import)

old_include = 'app.include_router(dashboard_router, prefix="/api")'
new_include = 'app.include_router(dashboard_router, prefix="/api")\napp.include_router(sentinel2_map_layer_router)'
if old_include not in src:
    raise SystemExit("ERROR: dashboard include_router line not found -- printing file:\n" + src)
src = src.replace(old_include, new_include)

if src == original:
    print("No changes were necessary (already patched?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("main.py patched -- sentinel2_map_layer router now included.")
