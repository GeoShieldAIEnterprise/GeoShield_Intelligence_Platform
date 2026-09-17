from pathlib import Path

path = Path("core/connectors/sentinel2/sentinel2_ndvi_connector.py")
src = path.read_text(encoding="utf-8-sig")
original = src

# 1. Add a named module-level constant near the other tuning constants.
anchor_1 = "MAX_CLOUD_COVERAGE = 50"
if anchor_1 not in src:
    raise SystemExit("ERROR: MAX_CLOUD_COVERAGE constant not found -- printing file:\n" + src)
src = src.replace(anchor_1, anchor_1 + "\nNDVI_RESOLUTION_DEG = 0.01  # ~1.1km at Kenyan latitude; EPSG:4326 bounds require degrees, not meters", 1)

# 2. Use the constant instead of the inline literals.
anchor_2 = '''                "resx": 0.01,
                "resy": 0.01,'''
if anchor_2 not in src:
    raise SystemExit("ERROR: inline resx/resy literals not found -- printing file:\n" + src)
src = src.replace(anchor_2, '''                "resx": NDVI_RESOLUTION_DEG,
                "resy": NDVI_RESOLUTION_DEG,''', 1)

if src == original:
    print("No changes were necessary.")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("sentinel2_ndvi_connector.py: patched -- NDVI_RESOLUTION_DEG constant added and wired in.")
