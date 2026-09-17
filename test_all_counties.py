import time
from core.connectors.sentinel2.sentinel2_ndvi_connector import build_sentinel2_ndvi_connector

connector = build_sentinel2_ndvi_connector()
print("Connector enabled:", connector.is_enabled())

start = time.time()
result = connector.search()
elapsed = time.time() - start

print("Success:", result.success)
print("Elapsed seconds:", round(elapsed, 1))

if result.success:
    data = result.data
    non_null = {k: v for k, v in data.items() if v is not None}
    null_counties = [k for k, v in data.items() if v is None]

    print("Total counties:", len(data))
    print("Counties with real NDVI:", len(non_null))
    print("Counties with null NDVI:", len(null_counties))
    if null_counties:
        print("Null counties:", null_counties)

    print()
    print("Sample values (first 10):")
    for name, val in list(non_null.items())[:10]:
        print(f"  {name}: {val}")
else:
    print("Error:", result.error)
