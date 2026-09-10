from pathlib import Path

html_path = Path("frontend/templates/index.html")
content = html_path.read_text(encoding="utf-8")

# Ensure all workspace and component stylesheets are correctly loaded in the head
required_css = """
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/workspace-switcher.css">
    <link rel="stylesheet" href="/static/satellite-center.css">
    <link rel="stylesheet" href="/static/sentinel2.css">
    <link rel="stylesheet" href="/static/workspace-nav.css">
    <link rel="stylesheet" href="/static/workspace.css">
    <link rel="stylesheet" href="/static/satellites.css">
    <link rel="stylesheet" href="/static/live-map.css">
"""

if "/static/workspace-switcher.css" not in content:
    content = content.replace("</head>", f"{required_css}\n</head>")
    html_path.write_text(content, encoding="utf-8")
    print("Restored all CSS links in index.html.")
else:
    print("CSS links already present.")
