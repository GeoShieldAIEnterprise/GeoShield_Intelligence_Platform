import shutil

path = r"frontend\static\counties.js"
backup = r"frontend\static\counties.js.debug_bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

shutil.copyfile(path, backup)

old = "                        click: function () {\n\n                            window.currentCounty = county;\n"

new = "                        click: function () {\n\n                            console.log(\"%c[COUNTY CLICK FIRED]\", \"background: red; color: white; font-size: 20px;\", county);\n\n                            window.currentCounty = county;\n"

count = content.count(old)
if count != 1:
    print(f"ABORTED -- expected 1 match, found {count}")
    raise SystemExit(1)

content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched successfully. Backup saved at " + backup)
