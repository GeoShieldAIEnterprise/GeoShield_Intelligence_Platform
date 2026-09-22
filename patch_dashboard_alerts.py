# -*- coding: utf-8 -*-
import io

path = r"backend\routes\dashboard.py"
with io.open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''    elevated = {"High", "Extreme"}
    alert_count = sum(
        1 for h in (fire, agriculture, drought, flood)
        if h.get("risk_level") in elevated
    )'''

new = '''    try:
        from engines.alerts.alert_engine import get_active_alert_count
        alert_count = get_active_alert_count()
    except Exception:
        # Fallback if the orchestrator hasn't started yet or import fails:
        # count hazards currently at High/Extreme for this request only.
        elevated = {"High", "Extreme"}
        alert_count = sum(
            1 for h in (fire, agriculture, drought, flood)
            if h.get("risk_level") in elevated
        )'''

count = content.count(old)
if count != 1:
    print("[FAIL] dashboard.py: expected exactly 1 match, found %d -- no changes made." % count)
    print("Paste back: Get-Content backend\\routes\\dashboard.py -Raw | Select-String -Pattern 'elevated' -Context 3,3")
else:
    content = content.replace(old, new, 1)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] dashboard.py: alert_count now sourced from alert orchestrator (with fallback)")
