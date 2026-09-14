"""
GeoShield FIRMS Connector

VIIRS active fire / thermal anomaly data via NASA FIRMS.
Implements the standard GeoShield BaseConnector interface.

Uses curl.exe (Windows Schannel) instead of Python's requests
library: this machine's OpenSSL 3.0.20 hits SSLEOFError against
several external HTTPS servers (confirmed with both Copernicus
and NASA FIRMS), while curl/Schannel handles them without issue.
"""

from __future__ import annotations

import csv
import io
import json
import subprocess
from typing import Any

from core.config import settings
from .base_connector import BaseConnector
from .connector_config import ConnectorConfig
from .connector_result import ConnectorResult

FIRMS_AREA_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
FIRMS_STATUS_URL = "https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/"

# Bounding box covering all of Kenya: west,south,east,north
KENYA_BBOX = "33.5,-5.0,42.0,5.5"


def _curl_get(url: str, timeout: float) -> tuple[bool, str]:
    """Fetch a URL via curl.exe. Returns (success, text_or_error)."""

    try:
        result = subprocess.run(
            ["curl.exe", "-s", "--max-time", str(int(timeout)), url],
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )

    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"curl failed to run: {exc}"

    if result.returncode != 0:
        return False, f"curl exited with code {result.returncode}: {result.stderr}"

    return True, result.stdout


class FIRMSConnector(BaseConnector):
    """VIIRS active fire / thermal anomaly connector via NASA FIRMS."""

    @property
    def provider_name(self) -> str:
        return "VIIRS-FIRMS"

    def connect(self) -> ConnectorResult:
        map_key = self.config.credentials.get("map_key", "")

        if not map_key:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error="FIRMS_MAP_KEY is not configured.",
            )

        url = f"{FIRMS_STATUS_URL}?MAP_KEY={map_key}"
        ok, text = _curl_get(url, min(self.config.timeout, 15))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Unable to reach FIRMS: {text}",
            )

        try:
            data = json.loads(text)

        except ValueError as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"FIRMS returned an invalid response: {exc}",
            )

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="connect",
            data=data,
        )

    def search(self, **filters: Any) -> ConnectorResult:
        map_key = self.config.credentials.get("map_key", "")

        if not map_key:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error="FIRMS_MAP_KEY is not configured.",
            )

        bbox = filters.get("bbox", KENYA_BBOX)
        sensor = filters.get("sensor", "VIIRS_SNPP_NRT")
        day_range = filters.get("day_range", 1)

        url = f"{FIRMS_AREA_BASE}/{map_key}/{sensor}/{bbox}/{day_range}"
        ok, text = _curl_get(url, min(self.config.timeout, 30))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Unable to reach FIRMS: {text}",
            )

        text = text.strip()

        if not text or text.lower().startswith("invalid"):
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"FIRMS returned an unexpected response: {text[:200]}",
            )

        reader = csv.DictReader(io.StringIO(text))
        detections = list(reader)

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=detections,
            metadata={
                "bbox": bbox,
                "sensor": sensor,
                "day_range": day_range,
                "count": len(detections),
            },
        )

    def download(self, product_id: str) -> ConnectorResult:
        return ConnectorResult.failure(
            provider=self.provider_name,
            operation="download",
            error="FIRMS does not support per-product downloads; use search() instead.",
        )


def build_firms_connector() -> FIRMSConnector:
    """Factory: builds a FIRMSConnector wired to GeoShield settings."""

    config = ConnectorConfig(
        connector_id="firms_viirs",
        provider="NASA-FIRMS",
        enabled=bool(settings.firms_map_key),
        base_url=FIRMS_AREA_BASE,
        timeout=settings.http_timeout,
        credentials={"map_key": settings.firms_map_key},
    )
    return FIRMSConnector(config)
