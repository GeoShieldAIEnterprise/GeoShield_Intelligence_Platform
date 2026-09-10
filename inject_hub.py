from pathlib import Path

# Insert the missing satelliteHub container into index.html inside the satellite intelligence workspace page
html_path = Path("frontend/templates/index.html")
html_content = html_path.read_text(encoding="utf-8")

target_str = '<section id="satelliteCenter" class="satellite-center">'
replacement_str = '<div id="satelliteHub"></div>\n            <section id="satelliteCenter" class="satellite-center">'

if target_str in html_content and 'id="satelliteHub"' not in html_content:
    html_content = html_content.replace(target_str, replacement_str, 1)
    html_path.write_text(html_content, encoding="utf-8")
    print("Successfully injected id='satelliteHub' into index.html.")
else:
    print("Target container not found or satelliteHub already exists.")
