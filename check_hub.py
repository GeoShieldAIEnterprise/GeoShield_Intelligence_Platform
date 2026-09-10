from pathlib import Path

# Let's inspect index.html to see if id="satelliteHub" is present in the DOM
html_path = Path("frontend/templates/index.html")
content = html_path.read_text(encoding="utf-8")
print("Does index.html contain 'satelliteHub'?", "satelliteHub" in content)
