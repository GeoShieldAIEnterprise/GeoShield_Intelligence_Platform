from pathlib import Path

# Let's inspect satellite-ui.js further to see what structure it expects inside satelliteHub
ui_path = Path("frontend/static/satellite-ui.js")
if ui_path.exists():
    print(ui_path.read_text(encoding="utf-8")[:1000])
