from pathlib import Path

# Inspect the current structure of index.html to find where to place satelliteHub accurately
html_path = Path("frontend/templates/index.html")
print(html_path.read_text(encoding="utf-8"))
