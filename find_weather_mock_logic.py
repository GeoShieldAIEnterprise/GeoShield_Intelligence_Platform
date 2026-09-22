import re
import glob

# Search anywhere in the codebase for where "mock" and "weather"/"era5" mode gets set
files = glob.glob("core/**/*.py", recursive=True) + glob.glob("backend/**/*.py", recursive=True)
files = [f for f in files if "GeoShield_venv" not in f]

hits = []
for f in files:
    try:
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.read()
    except Exception:
        continue
    if re.search(r'mock', content, re.IGNORECASE) and re.search(r'weather|era5', content, re.IGNORECASE):
        hits.append(f)

print("Files mentioning both 'mock' and 'weather/era5':")
for f in sorted(set(hits)):
    print(" ", f)
print()

for f in sorted(set(hits)):
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    print(f"=== {f} ===")
    for i, line in enumerate(content.splitlines(), 1):
        if re.search(r'mock', line, re.IGNORECASE):
            print(f"  L{i}: {line.strip()}")
    print()
