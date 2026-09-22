"""
GeoShield Terrain/Elevation Connector (via Open-Meteo)

Per-county terrain ruggedness proxy for flood risk, via Open-Meteo's
free Elevation API (backed by Copernicus DEM GLO-90, 90m resolution).

For each county, samples elevation at 5 points (the 4 bounding-box
corners + centroid) and computes the spread between them as a slope
proxy: a tight elevation spread means flat terrain, where rainwater
pools rather than draining away (higher flood risk at the same
rainfall); a wide spread means steep terrain that sheds water fast
(lower flood risk at the same rainfall).

Same request pattern as ERA5Connector (Open-Meteo, keyless, curl.exe,
comma-separated multi-coordinate in one request).
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import geopandas as gpd

from core.config import settings
from .base_connector import BaseConnector
from .connector_config import ConnectorConfig
from .connector_result import ConnectorResult

ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
COUNTIES_GEOJSON = Path("frontend/static/data/kenya_counties.geojson")
CACHE_MINUTES = 1440  # terrain never changes; cache for a full day to avoid unnecessary refetches


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


class ElevationConnector(BaseConnector):
    """Terrain/elevation connector via Open-Meteo (Copernicus DEM GLO-90 backed)."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._cache: dict[str, Any] | None = None
        self._cache_time: float = 0.0
        self._fail_time: float = 0.0
        self._lock = threading.Lock()

    @property
    def provider_name(self) -> str:
        return "Copernicus-DEM-OpenMeteo"

    def connect(self) -> ConnectorResult:
        url = f"{ELEVATION_URL}?latitude=-1.286389&longitude=36.817223"
        ok, text = _curl_get(url, min(self.config.timeout, 15))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Unable to reach Open-Meteo Elevation API: {text}",
            )

        try:
            data = json.loads(text)

        except ValueError as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Open-Meteo Elevation API returned an invalid response: {exc}",
            )

        return ConnectorResult.ok(provider=self.provider_name, operation="connect", data=data)

    def search(self, **filters: Any) -> ConnectorResult:
        now = time.time()

        if self._cache is not None and (now - self._cache_time) < (CACHE_MINUTES * 60):
            return ConnectorResult.ok(
                provider=self.provider_name,
                operation="search",
                data=self._cache,
                metadata={"cached": True, "cache_age_seconds": round(now - self._cache_time)},
            )

        if (now - self._fail_time) < 60:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error="Skipping retry: a recent request failed (likely rate-limited); backing off for 60s.",
            )

        if not self._lock.acquire(blocking=False):
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error="Another request is already fetching elevation data; try again shortly.",
            )

        try:
            counties = gpd.read_file(COUNTIES_GEOJSON)

        except Exception as exc:
            self._fail_time = now
            self._lock.release()
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Failed to load county boundaries: {exc}",
            )

        names: list[str] = []
        point_counts: list[int] = []
        lats: list[str] = []
        lons: list[str] = []

        for _, row in counties.iterrows():
            name = row.get("COUNTY") or row.get("NAME") or row.get("name")

            if not name:
                continue

            geometry = row.geometry

            # Use the actual polygon boundary, not the bounding box, so
            # sample points always fall on real county terrain -- bounding
            # box corners can land outside irregular/elongated counties
            # (e.g. Tana River, Turkana, Marsabit) and misrepresent their
            # true elevation profile.
            if geometry.geom_type == "MultiPolygon":
                largest = max(geometry.geoms, key=lambda g: g.area)
                boundary_coords = list(largest.exterior.coords)
            else:
                boundary_coords = list(geometry.exterior.coords)

            NUM_BOUNDARY_POINTS = 8
            step = max(1, len(boundary_coords) // NUM_BOUNDARY_POINTS)
            sampled_boundary = boundary_coords[::step][:NUM_BOUNDARY_POINTS]

            representative = geometry.representative_point()

            points = [(lat, lon) for lon, lat in sampled_boundary]
            points.append((representative.y, representative.x))

            names.append(name)
            point_counts.append(len(points))

            for lat, lon in points:
                lats.append(str(round(lat, 4)))
                lons.append(str(round(lon, 4)))

        BATCH_SIZE = 100
        elevations: list[float | None] = []

        for i in range(0, len(lats), BATCH_SIZE):
            batch_lats = lats[i:i + BATCH_SIZE]
            batch_lons = lons[i:i + BATCH_SIZE]

            lat_param = ",".join(batch_lats)
            lon_param = ",".join(batch_lons)

            url = f"{ELEVATION_URL}?latitude={lat_param}&longitude={lon_param}"

            ok, body = _curl_get(url, min(self.config.timeout, 30))

            if not ok:
                self._fail_time = now
                self._lock.release()
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Unable to reach Open-Meteo Elevation API (batch {i // BATCH_SIZE}): {body}",
                )

            try:
                data = json.loads(body)

            except ValueError as exc:
                self._fail_time = now
                self._lock.release()
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Open-Meteo Elevation API returned an invalid response (batch {i // BATCH_SIZE}): {exc}",
                )

            if data.get("error"):
                self._fail_time = now
                self._lock.release()
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Open-Meteo Elevation API error (batch {i // BATCH_SIZE}): {data.get('reason')}",
                )

            batch_elevations = data.get("elevation", [])

            if len(batch_elevations) != len(batch_lats):
                self._fail_time = now
                self._lock.release()
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Mismatch in batch {i // BATCH_SIZE}: {len(batch_lats)} points requested, {len(batch_elevations)} elevations returned.",
                )

            elevations.extend(batch_elevations)
            time.sleep(1)

        if len(elevations) != sum(point_counts):
            self._fail_time = now
            self._lock.release()
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Mismatch: {sum(point_counts)} points requested, {len(elevations)} elevations returned across all batches.",
            )

        results: dict[str, dict[str, Any]] = {}
        cursor = 0

        for name, count in zip(names, point_counts):
            chunk = elevations[cursor:cursor + count]
            cursor += count

            valid = [v for v in chunk if v is not None]

            if not valid:
                results[name] = {"mean_elevation_m": None, "elevation_range_m": None}
                continue

            results[name] = {
                "mean_elevation_m": round(sum(valid) / len(valid), 1),
                "elevation_range_m": round(max(valid) - min(valid), 1),
            }

        self._cache = results
        self._cache_time = now
        self._lock.release()

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=results,
            metadata={"cached": False, "county_count": len(results)},
        )

    def download(self, product_id: str) -> ConnectorResult:
        return ConnectorResult.failure(
            provider=self.provider_name,
            operation="download",
            error="Copernicus-DEM-OpenMeteo does not support per-product downloads; use search() instead.",
        )


def build_elevation_connector() -> ElevationConnector:
    """Factory: builds an ElevationConnector (Open-Meteo / Copernicus DEM backed)."""

    config = ConnectorConfig(
        connector_id="elevation_openmeteo",
        provider="Open-Meteo-Elevation",
        enabled=True,
        base_url=ELEVATION_URL,
        timeout=settings.http_timeout,
        credentials={},
    )
    return ElevationConnector(config)
