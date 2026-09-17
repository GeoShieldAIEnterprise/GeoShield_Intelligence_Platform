from pathlib import Path

def patch(path_str, anchor, addition, label):
    path = Path(path_str)
    src = path.read_text(encoding="utf-8-sig")
    original = src
    if anchor not in src:
        raise SystemExit(f"ERROR: anchor not found for {label} in {path_str} -- printing file:\n" + src)
    src = src.replace(anchor, addition, 1)
    if src == original:
        print(f"{label}: no changes were necessary.")
    else:
        path.write_text(src, encoding="utf-8", newline="\n")
        print(f"{label}: patched successfully.")

# earthquake_engine.py
patch(
    "backend/disaster/earthquake_engine.py",
    '''        self.data_manager.load_layer(
            "roads",
            str(PROJECT_ROOT / "data" / "roads" / "ken_roads.shp"),
        )''',
    '''        try:
            self.data_manager.load_layer(
                "roads",
                str(PROJECT_ROOT / "data" / "roads" / "ken_roads.shp"),
            )
        except FileNotFoundError as exc:
            print(f"[EarthquakeEngine] WARNING: roads layer unavailable ({exc}); road enrichment will be skipped.")''',
    "earthquake_engine.py"
)

# fire_engine.py
patch(
    "backend/disaster/fire_engine.py",
    '''        self.data_manager.load_layer(
            "roads",
            str(roads_path),
        )''',
    '''        try:
            self.data_manager.load_layer(
                "roads",
                str(roads_path),
            )
        except FileNotFoundError as exc:
            print(f"[FireEngine] WARNING: roads layer unavailable ({exc}); road enrichment will be skipped.")''',
    "fire_engine.py"
)

print()
print("ALL ROADS-RESILIENCE PATCHES APPLIED.")
