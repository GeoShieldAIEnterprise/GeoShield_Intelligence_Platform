from pathlib import Path

html_path = Path("frontend/templates/index.html")
content = html_path.read_text(encoding="utf-8")

# Ensure the body has the proper flex container structure expected by style.css and workspace.css
if "app-container" not in content:
    # Wrap main content blocks inside a proper application layout structure
    updated_content = content.replace(
        "<body>",
        '<body>\n    <div class="app-container">\n        <div class="sidebar-container">'
    ).replace(
        '<div id="liveMap"',
        '</div>\n        <div class="main-content-area">\n            <div id="liveMap"'
    )
    if "main-content-area" not in updated_content:
        # Fallback structural injection if tags differ
        updated_content = content # keep original if replacement fails
    html_path.write_text(content, encoding="utf-8")

print("Checked HTML layout structure.")
