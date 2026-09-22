import json
import urllib.request

req = urllib.request.Request("http://localhost:8000/api/agriculture/live")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

records = data if isinstance(data, list) else data.get("counties") or data.get("data") or []
if records:
    print("Sample record keys and values (first county):")
    sample = records[0] if isinstance(records, list) else next(iter(records.values()))
    for k, v in sample.items():
        print(f"  {k!r}: {v!r}")
else:
    print("Could not locate a per-county record list -- top-level keys were:", list(data.keys()))
