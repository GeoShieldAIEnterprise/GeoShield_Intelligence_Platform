import shutil

path = r"frontend\static\counties.js"
backup = r"frontend\static\counties.js.debug_bak2"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

shutil.copyfile(path, backup)

old = "                                .then(data => {\n                                    const overallEl = document.getElementById(\"aiScore\");\n                                    if (!overallEl) return;"

new = "                                .then(data => {\n                                    console.log(\"%c[DASHBOARD DATA RECEIVED]\", \"background: blue; color: white; font-size: 16px;\", data);\n                                    const overallEl = document.getElementById(\"aiScore\");\n                                    if (!overallEl) { console.error(\"[aiScore element NOT FOUND]\"); return; }"

count = content.count(old)
if count != 1:
    print(f"ABORTED -- expected 1 match, found {count}")
    raise SystemExit(1)

content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched successfully. Backup saved at " + backup)
