import sys
sys.path.insert(0, ".")

from core.auth.copernicus import CopernicusAuthManager
from core.connectors.sentinel2.sentinel2_ndvi_connector import (
    Sentinel2NDVIConnector, STATISTICS_URL, NDVI_EVALSCRIPT,
    NDVI_RESOLUTION_DEG, LOOKBACK_DAYS, MAX_CLOUD_COVERAGE, _curl_post_json,
)
from core.connectors.connector_config import ConnectorConfig
from core.config import settings
from datetime import datetime, timedelta, timezone
import json

config = ConnectorConfig(
    connector_id="sentinel2_ndvi_diag", provider="Copernicus-SentinelHub",
    enabled=True, base_url=STATISTICS_URL, timeout=settings.http_timeout, credentials={},
)
conn = Sentinel2NDVIConnector(config)

token = conn._auth.get_token()
print(f"Token acquired, length={len(token)}")

date_to = datetime.now(timezone.utc)
date_from = date_to - timedelta(days=LOOKBACK_DAYS)
date_to_str = date_to.strftime("%Y-%m-%dT%H:%M:%SZ")
date_from_str = date_from.strftime("%Y-%m-%dT%H:%M:%SZ")

counties = conn._county_geometries()
print(f"Loaded {len(counties)} county geometries\n")

null_count = 0
for i, (name, geometry) in enumerate(counties):
    payload = {
        "input": {
            "bounds": {"geometry": geometry, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
            "data": [{"type": "sentinel-2-l2a", "dataFilter": {"maxCloudCoverage": MAX_CLOUD_COVERAGE}}],
        },
        "aggregation": {
            "timeRange": {"from": date_from_str, "to": date_to_str},
            "aggregationInterval": {"of": f"P{LOOKBACK_DAYS}D"},
            "evalscript": NDVI_EVALSCRIPT,
            "resx": NDVI_RESOLUTION_DEG, "resy": NDVI_RESOLUTION_DEG,
        },
    }

    ok, text = _curl_post_json(STATISTICS_URL, token, payload, min(settings.http_timeout, 45))

    status = "CURL_FAIL" if not ok else "OK"
    if ok:
        try:
            body = json.loads(text)
            if "error" in body or "message" in body and "data" not in body:
                status = f"HTTP_ERROR: {json.dumps(body)[:200]}"
            else:
                intervals = body.get("data", [])
                found = False
                for interval in intervals:
                    stats = interval.get("outputs", {}).get("data", {}).get("bands", {}).get("B0", {}).get("stats", {})
                    if stats.get("sampleCount") and stats.get("mean") is not None:
                        found = True
                        status = f"OK mean={round(stats['mean'],4)} sampleCount={stats['sampleCount']}"
                        break
                if not found:
                    status = f"NO_VALID_INTERVAL raw_data={json.dumps(intervals)[:300]}"
        except (ValueError, KeyError, TypeError) as e:
            status = f"PARSE_FAIL: {e} raw_text={text[:300]}"
    else:
        status = f"CURL_FAIL: {text[:300]}"
        null_count += 1

    print(f"[{i+1:2d}/47] {name:20s} {status}")

print(f"\nTotal counties processed: {len(counties)}")
