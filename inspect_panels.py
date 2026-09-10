from pathlib import Path

# Let's inspect sentinel2.js, satellite-ui.js, and app.js to find the exact selectors/functions for the satellite intelligence panel
static_dir = Path("frontend/static")

for filename in ["sentinel2.js", "satellite-ui.js", "app.js"]:
    p = static_dir / filename
    if p.exists():
        print(f"=== {filename} ===")
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        for i, line in enumerate(lines[:30]):
            print(f"{i+1}: {line}")
        print("\n")
