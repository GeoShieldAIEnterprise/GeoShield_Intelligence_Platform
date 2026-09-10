from pathlib import Path
p = Path("frontend/static/satellite-ui.js")
print(p.read_text(encoding="utf-8"))
