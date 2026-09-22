path = r"backend\main.py"
backup = r"backend\main.py.debug_route_bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

import shutil
shutil.copyfile(path, backup)

# --- 1. Add import, right after dashboard_router import ---
old_import = "from backend.routes.dashboard import router as dashboard_router\n"
new_import = old_import + "from backend.routes.debug_seed_era5 import router as debug_seed_era5_router  # TEMP DEBUG -- remove after ERA5 verification\n"

if content.count(old_import) != 1:
    print(f"ABORTED at import -- expected 1 match, found {content.count(old_import)}")
    raise SystemExit(1)
content = content.replace(old_import, new_import, 1)

# --- 2. Add include_router, right after county_router include ---
old_include = "app.include_router(county_router)\n"
new_include = old_include + "app.include_router(debug_seed_era5_router)  # TEMP DEBUG -- remove after ERA5 verification\n"

if content.count(old_include) != 1:
    print(f"ABORTED at include_router -- expected 1 match, found {content.count(old_include)}")
    raise SystemExit(1)
content = content.replace(old_include, new_include, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Patched successfully. Backup saved at {backup}")
