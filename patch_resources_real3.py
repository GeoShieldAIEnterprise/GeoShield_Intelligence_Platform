from pathlib import Path

path = Path("backend/main.py")
src = path.read_text(encoding="utf-8-sig")
original = src

old_import = "from backend.database import get_db"
new_import = "from backend.database import get_db\nimport sqlite3\nfrom pathlib import Path as _Path"
if old_import not in src:
    raise SystemExit("ERROR: import line not found -- printing file:\n" + src)
src = src.replace(old_import, new_import)

old_endpoint = '''@app.get("/resources/{county_name}")
def get_county_resources(county_name: str):
    return {"county": county_name, "status": "active", "resources": ["Sentinel-2", "Water grids", "Emergency stations"]}'''

new_endpoint = '''@app.get("/resources/{county_name}")
def get_county_resources(county_name: str):
    db_path = _Path("database/geoshield.db")
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, category, county, latitude, longitude, status, capacity, contact "
        "FROM infrastructure WHERE county = ?",
        (county_name,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]'''

if old_endpoint not in src:
    raise SystemExit("ERROR: resources endpoint still not found -- printing file:\n" + src)
src = src.replace(old_endpoint, new_endpoint)

if src == original:
    print("No changes were necessary (already patched?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("main.py patched successfully -- /resources/{county} now returns real infrastructure records.")
