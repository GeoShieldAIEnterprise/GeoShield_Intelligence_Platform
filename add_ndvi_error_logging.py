path = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """        if not ok:
            return None

        try:
            body = json.loads(text)"""

new = """        if not ok:
            import logging
            logging.getLogger(__name__).warning("NDVI curl failed: %s", text[:300])
            return None

        try:
            body = json.loads(text)"""

if old not in content:
    print("Pattern not found -- may already be patched or file changed. No changes made.")
else:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print("Added error logging.")
