import shutil

path = r"core\connectors\era5_connector.py"
backup = r"core\connectors\era5_connector.py.bom_bak"

shutil.copyfile(path, backup)

with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"BOM stripped. Backup saved at {backup}")
