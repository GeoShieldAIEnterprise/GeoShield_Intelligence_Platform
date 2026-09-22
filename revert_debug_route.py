path = r"backend\main.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_import_line = "from backend.routes.debug_seed_era5 import router as debug_seed_era5_router  # TEMP DEBUG -- remove after ERA5 verification\n"
old_include_line = "app.include_router(debug_seed_era5_router)  # TEMP DEBUG -- remove after ERA5 verification\n"

if content.count(old_import_line) != 1 or content.count(old_include_line) != 1:
    print("ABORTED -- expected exactly 1 match each. No changes made.")
    print(f"import matches: {content.count(old_import_line)}, include matches: {content.count(old_include_line)}")
    raise SystemExit(1)

content = content.replace(old_import_line, "", 1)
content = content.replace(old_include_line, "", 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Debug route references removed from main.py")
