from pathlib import Path

# Adjust workspace CSS to prevent the map workspace from stretching over the panels and ensure correct panel visibility
css_path = Path("frontend/static/workspace.css")
if css_path.exists():
    css_content = css_path.read_text(encoding="utf-8")
else:
    css_content = ""

# Append or replace layout constraints for workspace views and bottom cards
layout_fix = """
/* Fix workspace panel proportions and prevent map dominance */
.workspace-view, .geoshield-workspace {
    display: flex;
    flex-direction: column;
    height: 100%;
    box-sizing: border-box;
}

#liveMap {
    flex: 1;
    width: 100%;
    min-height: 350px;
}

.satellite-intelligence-panel, .dashboard-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 10px;
}
"""

if "/* Fix workspace panel proportions" not in css_content:
    css_path.write_text(css_content + "\n" + layout_fix, encoding="utf-8")
    print("Updated workspace.css with panel proportion fixes.")
