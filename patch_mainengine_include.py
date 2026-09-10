from pathlib import Path

path = Path("backend/main.py")
src = path.read_text(encoding="utf-8-sig")
original = src

old_import = "from backend.api.sentinel2_map_layer import router as sentinel2_map_layer_router"
new_import = "from backend.api.sentinel2_map_layer import router as sentinel2_map_layer_router\nfrom backend.api.main_engine_api import router as main_engine_router"
if old_import not in src:
    raise SystemExit("ERROR: sentinel2_map_layer import not found -- printing file:\n" + src)
src = src.replace(old_import, new_import)

old_include = "app.include_router(sentinel2_map_layer_router)"
new_include = "app.include_router(sentinel2_map_layer_router)\napp.include_router(main_engine_router)"
if old_include not in src:
    raise SystemExit("ERROR: sentinel2_map_layer include not found -- printing file:\n" + src)
src = src.replace(old_include, new_include)

if src == original:
    print("No changes were necessary (already patched?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("main.py patched -- Main Engine API now included at /api/main-engine/*.")
