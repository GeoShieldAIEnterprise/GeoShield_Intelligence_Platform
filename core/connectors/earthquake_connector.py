"""
GeoShield Earthquake Connector (USGS)

Live earthquake feed via the USGS Earthquake Hazards Program.
Implements the standard GeoShield BaseConnector interface.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from core.config import settings
from .base_connector import BaseConnector
from .connector_config import ConnectorConfig
from .connector_result import ConnectorResult

USGS_FEED_BASE = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"


def _curl_get(url: str, timeout: float) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["curl.exe", "-s", "--max-time", str(int(timeout)), url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + 5,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"curl failed to run: {exc}"

    if result.returncode != 0:
        return False, f"curl exited with code {result.returncode}: {result.stderr}"

    return True, result.stdout


class EarthquakeConnector(BaseConnector):
    """Live earthquake feed connector via USGS."""

    @property
    def provider_name(self) -> str:
        return "USGS-Earthquake"

    def connect(self) -> ConnectorResult:
        url = f"{USGS_FEED_BASE}/all_hour.geojson"
        ok, text = _curl_get(url, min(self.config.timeout, 15))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Unable to reach USGS: {text}",
            )

        return ConnectorResult.ok(provider=self.provider_name, operation="connect", data={"reachable": True})

    def search(self, **filters: Any) -> ConnectorResult:
        """
        Optional: period ('hour'|'day'|'week'|'month', default 'day'),
                   min_magnitude (float), bbox (west, south, east, north)
        """
        period = filters.get("period", "day")
        if period not in {"hour", "day", "week", "month"}:
            period = "day"

        url = f"{USGS_FEED_BASE}/all_{period}.geojson"
        ok, text = _curl_get(url, min(self.config.timeout, 30))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Unable to reach USGS: {text}",
            )

        try:
            payload = json.loads(text)
        except ValueError as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"USGS returned an invalid response: {exc}",
            )

        min_magnitude = filters.get("min_magnitude")
        bbox = filters.get("bbox")
        events = []

        for feature in payload.get("features", []):
            prop = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = (geom.get("coordinates") or [None, None, None]) + [None, None, None]
            lon, lat, depth = coords[0], coords[1], coords[2]
            mag = prop.get("mag")

            if mag is None or lon is None or lat is None:
                continue

            if min_magnitude is not None and mag < min_magnitude:
                continue

            if bbox is not None:
                west, south, east, north = bbox
                if not (west <= lon <= east and south <= lat <= north):
                    continue

            events.append({
                "id": feature.get("id"),
                "place": prop.get("place"),
                "magnitude": mag,
                "depth_km": depth,
                "time": prop.get("time"),
                "updated": prop.get("updated"),
                "tsunami": prop.get("tsunami"),
                "alert": prop.get("alert"),
                "url": prop.get("url"),
                "latitude": lat,
                "longitude": lon,
            })

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=events,
            metadata={"period": period, "count": len(events), "min_magnitude": min_magnitude},
        )

    def download(self, product_id: str) -> ConnectorResult:
        return ConnectorResult.failure(
            provider=self.provider_name,
            operation="download",
            error="USGS-Earthquake does not support per-event downloads; use search() instead.",
        )


def build_earthquake_connector() -> EarthquakeConnector:
    """Factory: builds an EarthquakeConnector (USGS backed)."""

    config = ConnectorConfig(
        connector_id="usgs_earthquake",
        provider="USGS",
        enabled=True,
        base_url=USGS_FEED_BASE,
        timeout=settings.http_timeout,
        credentials={},
    )
    return EarthquakeConnector(config)
