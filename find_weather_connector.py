import re

candidates = [
    "core/connectors/era5_connector.py",
    "core/connectors/weather_connector.py",
]

import glob
found = glob.glob("core/connectors/**/*weather*.py", recursive=True) + \
        glob.glob("core/connectors/**/*era5*.py", recursive=True)
found = sorted(set(found))

print("Found weather-related connector files:")
for f in found:
    print(" ", f)
print()

for f in found:
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    if "mock" in content.lower():
        print(f"=== {f} -- mock-related lines ===")
        for i, line in enumerate(content.splitlines(), 1):
            if "mock" in line.lower():
                print(f"  L{i}: {line.strip()}")
        print()
