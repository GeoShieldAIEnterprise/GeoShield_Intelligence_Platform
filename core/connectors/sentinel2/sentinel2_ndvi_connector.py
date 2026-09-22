"""
GeoShield Sentinel-2 NDVI Connector

Real per-county NDVI (vegetation health) via Copernicus Data Space's
Sentinel Hub Statistical API. Reuses the existing CopernicusAuthManager
OAuth2 token (curl-based, Schannel) -- the same auth already proven
working for the Sentinel-2 WMS tile layer.

Unlike the WMS tile layer (visual only), the Statistical API returns
real numeric NDVI values aggregated per county polygon, which is what
the Agriculture risk table needs.

Implements the standard GeoShield BaseConnector interface, mirroring
GPMConnector's caching/zonal-per-county shape.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import logging

import geopandas as gpd

from core.auth.copernicus import CopernicusAuthManager
from core.auth.exceptions import (
    CopernicusAuthenticationError,
    CopernicusConfigurationError,
    CopernicusNetworkError,
)
from core.config import settings
from ..base_connector import BaseConnector
from ..connector_config import ConnectorConfig
from ..connector_result import ConnectorResult

logger = logging.getLogger(__name__)

STATISTICS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
COUNTIES_GEOJSON = Path("frontend/static/data/kenya_counties.geojson")
CACHE_MINUTES = 180
LOOKBACK_DAYS = 14
MAX_CLOUD_COVERAGE = 50
NDVI_RESOLUTION_DEG = 0.01  # ~1.1km at Kenyan latitude; EPSG:4326 bounds require degrees, not meters

_search_lock = threading.Lock()

MAX_RETRIES_ON_RATE_LIMIT = 3
RETRY_BACKOFF_SECONDS = 5
REQUEST_DELAY_SECONDS = 0.8

NDVI_EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: [{bands: ["B04", "B08", "dataMask"]}],
    output: [
      {id: "data", bands: 1, sampleType: "FLOAT32"},
      {id: "dataMask", bands: 1}
    ]
  };
}
function evaluatePixel(sample) {
  var denom = sample.B08 + sample.B04;
  var ndvi = denom === 0 ? 0 : (sample.B08 - sample.B04) / denom;
  return {
    data: [ndvi],
    dataMask: [sample.dataMask]
  };
}"""


def _curl_post_json(url: str, token: str, payload: dict, timeout: float) -> tuple[bool, str]:
    """POST a JSON payload via curl.exe with a Bearer token. Returns (success, text_or_error)."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f)
        payload_path = f.name

    cmd = [
        "curl.exe", "-s", "--max-time", str(int(timeout)),
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "--data", f"@{payload_path}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)

    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"curl failed to run: {exc}"

    finally:
        try:
            Path(payload_path).unlink(missing_ok=True)
        except OSError:
            pass

    if result.returncode != 0:
        return False, f"curl exited with code {result.returncode}: {result.stderr}"

    return True, result.stdout


class Sentinel2NDVIConnector(BaseConnector):
    """Sentinel-2 NDVI connector via Copernicus Sentinel Hub Statistical API."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._auth = CopernicusAuthManager()
        self._cache: dict[str, Any] | None = None
        self._cache_time: float = 0.0
        # Stale-while-revalidate: NDVI changes slowly, so a county that fails
        # to fetch this cycle should keep showing its last successful reading
        # rather than going blank. These never expire on their own -- only a
        # fresh successful fetch overwrites them.
        self._last_good: dict[str, float] = {}
        self._last_good_time: dict[str, float] = {}

    @property
    def provider_name(self) -> str:
        return "Sentinel2-NDVI"

    def connect(self) -> ConnectorResult:
        try:
            self._auth.get_token()

        except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError) as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=str(exc),
            )

        return ConnectorResult.ok(provider=self.provider_name, operation="connect", data={"reachable": True})

    def _county_geometries(self) -> list[tuple[str, dict]]:
        counties = gpd.read_file(COUNTIES_GEOJSON)
        out: list[tuple[str, dict]] = []

        for _, row in counties.iterrows():
            name = row.get("COUNTY") or row.get("NAME") or row.get("name")

            if not name:
                continue

            out.append((name, row.geometry.__geo_interface__))

        return out

    def _query_county_ndvi(self, token: str, geometry: dict, date_from: str, date_to: str) -> float | None:
        payload = {
            "input": {
                "bounds": {
                    "geometry": geometry,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {"maxCloudCoverage": MAX_CLOUD_COVERAGE},
                    }
                ],
            },
            "aggregation": {
                "timeRange": {"from": date_from, "to": date_to},
                "aggregationInterval": {"of": f"P{LOOKBACK_DAYS}D"},
                "evalscript": NDVI_EVALSCRIPT,
                "resx": NDVI_RESOLUTION_DEG,
                "resy": NDVI_RESOLUTION_DEG,
            },
        }

        ok, text = _curl_post_json(STATISTICS_URL, token, payload, min(settings.http_timeout, 45))

        if not ok:
            import logging
            logging.getLogger(__name__).warning("NDVI curl failed: %s", text[:300])
            return None

        try:
            body = json.loads(text)
            intervals = body.get("data", [])

            for interval in intervals:
                stats = (
                    interval.get("outputs", {})
                    .get("data", {})
                    .get("bands", {})
                    .get("B0", {})
                    .get("stats", {})
                )

                sample_count = stats.get("sampleCount", 0)
                mean = stats.get("mean")

                if sample_count and mean is not None:
                    return round(float(mean), 4)

            import logging
            logging.getLogger(__name__).warning(
                "NDVI no valid interval found. Raw response body: %s", text[:500]
            )
            return None

        except (ValueError, KeyError, TypeError) as exc:
            import logging
            logging.getLogger(__name__).warning(
                "NDVI parse failed (%s). Raw response body: %s", exc, text[:500]
            )
            return None

    def search(self, **filters: Any) -> ConnectorResult:
        with _search_lock:
            now = time.time()

            if self._cache is not None and (now - self._cache_time) < (CACHE_MINUTES * 60):
                return ConnectorResult.ok(
                    provider=self.provider_name,
                    operation="search",
                    data=self._cache,
                    metadata={"cached": True, "cache_age_seconds": round(now - self._cache_time)},
                )

            try:
                token = self._auth.get_token()

            except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError) as exc:
                if self._last_good:
                    logger.warning(
                        "Sentinel2-NDVI auth failed (%s); serving last-known-good NDVI for all counties.", exc
                    )
                    return ConnectorResult.ok(
                        provider=self.provider_name,
                        operation="search",
                        data=dict(self._last_good),
                        metadata={
                            "cached": True,
                            "stale_fallback": True,
                            "stale_counties": sorted(self._last_good.keys()),
                            "reason": str(exc),
                        },
                    )
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=str(exc),
                )

            date_to = datetime.now(timezone.utc)
            date_from = date_to - timedelta(days=LOOKBACK_DAYS)
            date_to_str = date_to.strftime("%Y-%m-%dT%H:%M:%SZ")
            date_from_str = date_from.strftime("%Y-%m-%dT%H:%M:%SZ")

            try:
                counties = self._county_geometries()

            except Exception as exc:
                if self._last_good:
                    logger.warning(
                        "Failed to load county boundaries (%s); serving last-known-good NDVI.", exc
                    )
                    return ConnectorResult.ok(
                        provider=self.provider_name,
                        operation="search",
                        data=dict(self._last_good),
                        metadata={
                            "cached": True,
                            "stale_fallback": True,
                            "stale_counties": sorted(self._last_good.keys()),
                            "reason": str(exc),
                        },
                    )
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Failed to load county boundaries: {exc}",
                )

            results: dict[str, float | None] = {}
            stale_counties: list[str] = []

            for name, geometry in counties:
                fresh = None
                for attempt in range(MAX_RETRIES_ON_RATE_LIMIT + 1):
                    fresh = self._query_county_ndvi(token, geometry, date_from_str, date_to_str)
                    if fresh is not None:
                        break
                    if attempt < MAX_RETRIES_ON_RATE_LIMIT:
                        logger.warning(
                            "NDVI fetch for %s failed (attempt %d/%d) -- backing off %ds before retry.",
                            name, attempt + 1, MAX_RETRIES_ON_RATE_LIMIT, RETRY_BACKOFF_SECONDS,
                        )
                        time.sleep(RETRY_BACKOFF_SECONDS)

                time.sleep(REQUEST_DELAY_SECONDS)

                if fresh is not None:
                    results[name] = fresh
                    self._last_good[name] = fresh
                    self._last_good_time[name] = now
                elif name in self._last_good:
                    results[name] = self._last_good[name]
                    stale_counties.append(name)
                    age_min = (now - self._last_good_time.get(name, now)) / 60
                    logger.warning(
                        "NDVI fetch failed for %s this cycle; serving last-known-good value from %.0f min ago.",
                        name, age_min,
                    )
                else:
                    results[name] = None
                    logger.warning("NDVI fetch failed for %s and no prior value exists; returning null.", name)

            self._cache = results
            self._cache_time = now

            return ConnectorResult.ok(
                provider=self.provider_name,
                operation="search",
                data=results,
                metadata={
                    "cached": False,
                    "lookback_days": LOOKBACK_DAYS,
                    "stale_counties": stale_counties,
                },
            )

    def download(self, product_id: str) -> ConnectorResult:
        return ConnectorResult.failure(
            provider=self.provider_name,
            operation="download",
            error="Sentinel2-NDVI does not support per-product downloads; use search() instead.",
        )


def build_sentinel2_ndvi_connector() -> Sentinel2NDVIConnector:
    """Factory: builds a Sentinel2NDVIConnector wired to GeoShield settings."""

    config = ConnectorConfig(
        connector_id="sentinel2_ndvi",
        provider="Copernicus-SentinelHub",
        enabled=bool(settings.cdse_username and settings.cdse_password and settings.cdse_client_id),
        base_url=STATISTICS_URL,
        timeout=settings.http_timeout,
        credentials={},
    )
    return Sentinel2NDVIConnector(config)
