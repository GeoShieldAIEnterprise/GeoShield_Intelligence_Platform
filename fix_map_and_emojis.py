from pathlib import Path

# 1. Clean and update index.html template
html_path = Path("frontend/templates/index.html")
content = html_path.read_text(encoding="utf-8")

# Replace common mojibake patterns with clean HTML entities or text
replacements = {
    "ðŸ“Š Dashboard": "&#128202; Dashboard",
    "ðŸš€ Live Map": "&#128640; Live Map",
    "ðŸ“ˆ Analytics": "&#128200; Analytics",
    "ðŸ”” Alerts": "&#128276; Alerts",
    "ðŸ“ Reports": "&#128196; Reports",
    "ðŸ🌊 Flood Engine": "&#127754; Flood Engine",
    "ðŸ🔥 Fire Engine": "&#128293; Fire Engine",
    "ðŸ🌍 Earthquake Engine": "&#127757; Earthquake Engine",
    "ðŸ🌾 Agriculture": "&#127806; Agriculture",
    "⚙️ Settings": "&#9881;&#65039; Settings",
}

for bad, good in replacements.items():
    content = content.replace(bad, good)

# Also fix the live map title container if it has mojibake
content = content.replace("ðŸ>°ï¸ Live Map", "&#128640; Live Map")

html_path.write_text(content, encoding="utf-8")
print("index.html cleaned of mojibake.")

# 2. Ensure liveMap container has explicit height in CSS
css_path = Path("frontend/static/live-map.css")
if not css_path.exists():
    css_path = Path("frontend/static/style.css")

css_content = css_path.read_text(encoding="utf-8")
if "#liveMap" not in css_content:
    css_content += "\n\n#liveMap { width: 100%; height: calc(100vh - 200px); min-height: 500px; border-radius: 8px; }\n"
    css_path.write_text(css_content, encoding="utf-8")
    print("Added #liveMap height rules to CSS.")
else:
    print("#liveMap CSS already present.")
