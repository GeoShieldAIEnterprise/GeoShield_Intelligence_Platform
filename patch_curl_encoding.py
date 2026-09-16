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

OLD_BLOCK = """        result = subprocess.run(
            ["curl.exe", "-s", "--max-time", str(int(timeout)), url],
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )"""

NEW_BLOCK = """        result = subprocess.run(
            ["curl.exe", "-s", "--max-time", str(int(timeout)), url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + 5,
        )"""

patch("core/connectors/earthquake_connector.py", OLD_BLOCK, NEW_BLOCK, "earthquake_connector.py (curl encoding fix)")
patch("core/connectors/population_connector.py", OLD_BLOCK, NEW_BLOCK, "population_connector.py (curl encoding fix)")

print()
print("BOTH CONNECTORS PATCHED -- restart uvicorn and re-test.")
