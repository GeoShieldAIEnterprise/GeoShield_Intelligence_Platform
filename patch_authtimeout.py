from pathlib import Path

path = Path("core/auth/copernicus.py")
src = path.read_text(encoding="utf-8-sig")
original = src

old = "                    timeout=settings.http_timeout,"
new = "                    timeout=min(settings.http_timeout, 15),  # auth handshake should never need the full data-download timeout"

if old not in src:
    raise SystemExit("ERROR: timeout line not found -- printing file:\n" + src)
src = src.replace(old, new)
path.write_text(src, encoding="utf-8", newline="\n")
print("copernicus.py patched -- token requests now capped at 15s instead of the full 60s, so a bad first attempt fails fast and the retry kicks in quickly.")
