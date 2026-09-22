import shutil

path = r"backend\routes\dashboard.py"
backup = r"backend\routes\dashboard.py.bak"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

shutil.copyfile(path, backup)

old = '''    overall_risk = "--"
    if county:
        county_analytics = analytics_engine.get_county_analytics(county=county)
        counties = county_analytics.get("counties", [])
        if counties:
            overall_risk = counties[0].get("overall_risk") or "--"

    return {
        "system_status": "Online",
        "weather": "Live -- see county detail",
        "alerts": alert_count,
        "overall_risk": overall_risk,'''

new = '''    overall_risk = "--"
    overall_risk_percent = None
    if county:
        county_analytics = analytics_engine.get_county_analytics(county=county)
        counties = county_analytics.get("counties", [])
        if counties:
            overall_risk = counties[0].get("overall_risk") or "--"
            mean_rank = counties[0].get("mean_rank")
            if mean_rank is not None:
                # SEVERITY_RANK scale is 0 (Low) to 3 (Extreme)
                overall_risk_percent = round((mean_rank / 3) * 100)

    return {
        "system_status": "Online",
        "weather": "Live -- see county detail",
        "alerts": alert_count,
        "overall_risk": overall_risk,
        "overall_risk_percent": overall_risk_percent,'''

count = content.count(old)
if count != 1:
    print(f"ABORTED -- expected 1 match, found {count}")
    raise SystemExit(1)

content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched successfully. Backup saved at " + backup)
