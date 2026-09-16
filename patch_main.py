from pathlib import Path

path = Path("backend/main.py")
src = path.read_text(encoding="utf-8-sig")
original = src

import_anchor = "from backend.api.main_engine_api import router as main_engine_router"
import_addition = (
    import_anchor
    + "\nfrom backend.api.earthquake_api import router as earthquake_router"
    + "\nfrom backend.disaster.earthquake_engine import earthquake_engine"
    + "\nfrom core.engines.main_engine import main_engine"
)

if import_anchor not in src:
    raise SystemExit("ERROR: main_engine_api import not found -- printing file:\n" + src)

src = src.replace(import_anchor, import_addition, 1)

include_anchor = "app.include_router(county_router)"
include_addition = (
    include_anchor
    + "\napp.include_router(earthquake_router)"
    + "\nmain_engine.register_engine(\"earthquake\", earthquake_engine)"
)

if include_anchor not in src:
    raise SystemExit("ERROR: county_router include not found -- printing file:\n" + src)

src = src.replace(include_anchor, include_addition, 1)

if src == original:
    print("No changes were necessary (already patched?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("backend/main.py patched -- earthquake router included, earthquake engine registered with MainEngine.")
