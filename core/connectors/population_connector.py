"""
GeoShield Population Connector (WorldPop)

Provides on-demand population-exposure statistics for a buffer
around any point of interest (e.g. an earthquake epicenter), via
the WorldPop REST API (wpgppop dataset). This is queried live per
request, but the underlying population surface itself is WorldPop's
most recent modeled year (2020) -- there is no continuously-updating
live population census to connect to. Reusable by any engine that
needs population exposure (Earthquake, Alerts, etc.) via the Main
Engine, same as FIRMS/GPM/ERA5.

Uses curl.exe for network access, consistent with the other
connectors on this machine.
"""

from __future__ import annotations

import json
import math
import subprocess
import time
import urllib.parse
from typing import Any

from core.config import settings
from .base_connector import BaseConnector
from .connector_config import ConnectorConfig
from .connector_result import ConnectorResult

WORLDPOP_STATS_URL = "https://api.worldpop.org/v1/services/stats"
WORLDPOP_TASK_URL = "https://api.worldpop.org/v1/tasks"
DEFAULT_YEAR = 2020  # most recent WorldPop Global Project (wpgppop) modeled year
DEFAULT_RADIUS_KM = 50.0
CACHE_SECONDS = 3600


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


def _circle_polygon(lat: float, lon: float, radius_km: float, points: int = 32) -> dict:
    """Approximate a circular buffer around (lat, lon) as a GeoJSON polygon."""

    coords = []
    for i in range(points + 1):
        angle = 2 * math.pi * (i / points)
        d_lat = (radius_km / 111.32) * math.cos(angle)
        d_lon = (radius_km / (111.32 * math.cos(math.radians(lat)))) * math.sin(angle)
        coords.append([lon + d_lon, lat + d_lat])

    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        }],
    }


class PopulationConnector(BaseConnector):
    """Population-exposure connector via the WorldPop REST API."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_time: dict[str, float] = {}

    @property
    def provider_name(self) -> str:
        return "WorldPop"

    def connect(self) -> ConnectorResult:
        ok, text = _curl_get("https://api.worldpop.org/v1/services", min(self.config.timeout, 15))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Unable to reach WorldPop: {text}",
            )

        try:
            data = json.loads(text)
        except ValueError as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"WorldPop returned an invalid response: {exc}",
            )

        return ConnectorResult.ok(provider=self.provider_name, operation="connect", data=data)

    def search(self, **filters: Any) -> ConnectorResult:
        """
        Required: latitude, longitude
        Optional: radius_km (default 50.0), year (default 2020)
        """
        try:
            lat = float(filters["latitude"])
            lon = float(filters["longitude"])
        except (KeyError, TypeError, ValueError):
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error="latitude and longitude are required.",
            )

        radius_km = float(filters.get("radius_km", DEFAULT_RADIUS_KM))
        year = int(filters.get("year", DEFAULT_YEAR))

        cache_key = f"{round(lat, 3)}:{round(lon, 3)}:{radius_km}:{year}"
        now = time.time()

        if cache_key in self._cache and (now - self._cache_time[cache_key]) < CACHE_SECONDS:
            return ConnectorResult.ok(
                provider=self.provider_name,
                operation="search",
                data=self._cache[cache_key],
                metadata={"cached": True, "radius_km": radius_km, "year": year},
            )

        geojson = json.dumps(_circle_polygon(lat, lon, radius_km))
        url = f"{WORLDPOP_STATS_URL}?dataset=wpgppop&year={year}&geojson={urllib.parse.quote(geojson)}&runasync=false"

        api_key = self.config.credentials.get("api_key", "")
        if api_key:
            url += f"&key={api_key}"

        ok, text = _curl_get(url, min(self.config.timeout, 40))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Unable to reach WorldPop: {text}",
            )

        try:
            payload = json.loads(text)
        except ValueError as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"WorldPop returned an invalid response: {exc}",
            )

        if payload.get("error"):
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=payload.get("error_message") or "WorldPop reported an error.",
            )

        if payload.get("status") != "finished":
            taskid = payload.get("taskid")
            if not taskid:
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error="WorldPop did not return a taskid to poll.",
                )
            payload = self._poll_task(taskid)
            if payload is None:
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error="WorldPop task did not finish within the polling window.",
                )

        population = payload.get("data", {}).get("total_population")

        if population is None:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error="WorldPop response did not include total_population.",
            )

        result = {
            "population": float(population),
            "radius_km": radius_km,
            "year": year,
            "latitude": lat,
            "longitude": lon,
        }

        self._cache[cache_key] = result
        self._cache_time[cache_key] = now

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=result,
            metadata={"cached": False, "radius_km": radius_km, "year": year},
        )

    def _poll_task(self, taskid: str, max_wait: float = 30.0, interval: float = 2.0) -> dict | None:
        waited = 0.0
        while waited < max_wait:
            ok, text = _curl_get(f"{WORLDPOP_TASK_URL}/{taskid}", 15)
            if ok:
                try:
                    payload = json.loads(text)
                    if payload.get("status") == "finished":
                        return payload
                except ValueError:
                    pass
            time.sleep(interval)
            waited += interval
        return None

    def download(self, product_id: str) -> ConnectorResult:
        return ConnectorResult.failure(
            provider=self.provider_name,
            operation="download",
            error="WorldPop does not support per-product downloads; use search() instead.",
        )


def build_population_connector() -> PopulationConnector:
    """Factory: builds a PopulationConnector wired to GeoShield settings."""

    config = ConnectorConfig(
        connector_id="worldpop",
        provider="WorldPop",
        enabled=True,
        base_url=WORLDPOP_STATS_URL,
        timeout=settings.http_timeout,
        credentials={"api_key": getattr(settings, "worldpop_api_key", "")},
    )
    return PopulationConnector(config)