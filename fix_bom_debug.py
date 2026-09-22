import shutil

path = r"backend\routes\debug_seed_era5.py"
backup = r"backend\routes\debug_seed_era5.py.bom_bak"

shutil.copyfile(path, backup)

with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"BOM stripped. Backup saved at {backup}")
