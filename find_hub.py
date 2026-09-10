from pathlib import Path

# Let's search for any references to satelliteHub across the project
root_dir = Path("frontend")
for p in root_dir.rglob("*.*"):
    if p.suffix in [".js", ".html", ".css"]:
        try:
            content = p.read_text(encoding="utf-8")
            if "satelliteHub" in content:
                print(f"Found in {p}")
        except Exception:
            pass
