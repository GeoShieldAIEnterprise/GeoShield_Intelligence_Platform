from pathlib import Path

# Let's inspect frontend static files to see where workspace switching panels or satellite panels are defined
static_dir = Path("frontend/static")
print("Listing static files:")
for f in static_dir.glob("*.js"):
    print(f" - {f.name}")

app_js_path = static_dir / "app.js"
if app_js_path.exists():
    print("\n--- app.js preview ---")
    print(app_js_path.read_text(encoding="utf-8")[:500])
