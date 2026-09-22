import threading
import time

from core.connectors.sentinel2.sentinel2_ndvi_connector import build_sentinel2_ndvi_connector

connector = build_sentinel2_ndvi_connector()

# Force a cold cache, guaranteed
connector._cache = None
connector._cache_time = 0

results = []

def run_search(thread_id):
    start = time.time()
    try:
        result = connector.search()
        elapsed = time.time() - start
        results.append((thread_id, "OK", elapsed, result.metadata))
    except Exception as exc:
        elapsed = time.time() - start
        results.append((thread_id, "FAILED", elapsed, repr(exc)))

threads = [threading.Thread(target=run_search, args=(i,)) for i in range(5)]

start_all = time.time()
for t in threads:
    t.start()
for t in threads:
    t.join()
total = time.time() - start_all

print(f"\nTotal wall time for 5 concurrent search() calls: {total:.2f}s\n")
for thread_id, status, elapsed, info in sorted(results, key=lambda r: r[2]):
    print(f"Thread {thread_id}: {status} after {elapsed:.2f}s -> {info}")
