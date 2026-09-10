from pathlib import Path

# Create frontend/static/live-map.css since it is missing (resulting in 404 and unstyled map container)
css_path = Path("frontend/static/live-map.css")
css_path.parent.mkdir(parents=True, exist_ok=True)
css_content = """
#liveMap {
    width: 100%;
    height: 70vh;
    min-height: 500px;
    border-radius: 8px;
    z-index: 1;
}
.scene-info {
    font-size: 13px;
    color: #a0aec0;
    margin-bottom: 8px;
}
"""
css_path.write_text(css_content.strip(), encoding="utf-8")
print("Created missing live-map.css successfully.")
