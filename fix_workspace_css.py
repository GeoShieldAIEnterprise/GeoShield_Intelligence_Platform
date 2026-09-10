from pathlib import Path

# Let's inspect the CSS files causing the flex layout to fail.
# We'll create a single unified style override script to fix the layout positioning immediately.

css_fix_path = Path("frontend/static/workspace.css")
content = """
/* Workspace & Main Layout Fix */
body.geoshield-body, html, body {
    margin: 0;
    padding: 0;
    background-color: #0d1117;
    color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    height: 100vh;
    overflow: hidden;
}

.geoshield-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
}

.geoshield-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    height: 60px;
}

.geoshield-main-layout {
    display: flex;
    flex: 1;
    height: calc(100vh - 60px);
    overflow: hidden;
}

.geoshield-sidebar {
    width: 240px;
    background-color: #111418;
    border-right: 1px solid #30363d;
    display: flex;
    flex-direction: column;
    padding: 15px 10px;
    gap: 8px;
}

.geoshield-sidebar .nav-item {
    color: #c9d1d9;
    text-decoration: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.geoshield-sidebar .nav-item:hover, .geoshield-sidebar .nav-item.active {
    background-color: #1f6feb;
    color: #ffffff;
}

.geoshield-workspace {
    flex: 1;
    background-color: #0d1117;
    position: relative;
    overflow-y: auto;
    padding: 20px;
}

.workspace-view {
    display: none;
}

.workspace-view.active {
    display: block;
}

.map-container {
    width: 100%;
    height: calc(100vh - 160px);
    min-height: 450px;
    border-radius: 8px;
    border: 1px solid #30363d;
}
"""
css_fix_path.write_text(content.strip(), encoding="utf-8")
print("Applied flex layout override to workspace.css successfully.")
