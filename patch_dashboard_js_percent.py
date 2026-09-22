import shutil

path = r"frontend\static\dashboard.js"
backup = r"frontend\static\dashboard.js.bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

shutil.copyfile(path, backup)

old = '''            const overallEl = document.getElementById("aiScore");
            const overallRisk = data.overall_risk ?? "--";
            overallEl.innerText = overallRisk;
            const overallColors = {
                "Low": "#00b894", "Moderate": "#f1c40f",
                "High": "#e67e22", "Extreme": "#e74c3c"
            };
            overallEl.style.color = overallColors[overallRisk] || "";'''

new = '''            const overallEl = document.getElementById("aiScore");
            const overallRisk = data.overall_risk ?? "--";
            const overallPercent = data.overall_risk_percent;
            overallEl.innerText = (overallPercent != null) ? overallPercent + "%" : "--";
            const overallColors = {
                "Low": "#00b894", "Moderate": "#f1c40f",
                "High": "#e67e22", "Extreme": "#e74c3c"
            };
            overallEl.style.color = overallColors[overallRisk] || "";'''

count = content.count(old)
if count != 1:
    print(f"ABORTED -- expected 1 match, found {count}")
    raise SystemExit(1)

content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched successfully. Backup saved at " + backup)
