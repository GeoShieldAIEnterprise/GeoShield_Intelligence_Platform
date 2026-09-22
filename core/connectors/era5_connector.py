"""
GeoShield ERA5/Climate Connector (via Open-Meteo)

Live current-conditions weather data via Open-Meteo (open-meteo.com),
an ECMWF-based provider used here in place of the official Copernicus
CDS API for ERA5 -- CDS requests are queued and can take hours to
fulfill, which does not fit a live dashboard. Open-Meteo integrates
ECMWF among 15+ national weather services and responds instantly,
free, with no registration required.

Implements the standard GeoShield BaseConnector interface. Uses
curl.exe for network access, consistent with the other connectors
on this machine.
"""

from __future__ import annotations

import json
import os
import subprocess
import logging
import time
from pathlib import Path
from typing import Any

import geopandas as gpd

from core.config import settings
from .base_connector import BaseConnector
from .connector_config import ConnectorConfig
from .connector_result import ConnectorResult

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
COUNTIES_GEOJSON = Path("frontend/static/data/kenya_counties.geojson")
CACHE_MINUTES = 240  # lengthened -- Open-Meteo free tier has a DAILY quota, not just a burst limit
LAST_GOOD_CACHE_FILE = Path(settings.data_dir) / "era5_last_good.json"  # on-disk backup so a server restart does not lose last-known-good weather


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


class ERA5Connector(BaseConnector):
    """Live climate/weather connector via Open-Meteo (ECMWF-based)."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._cache: dict[str, Any] | None = None
        self._cache_time: float = 0.0
        # Stale-while-revalidate: Open-Meteo's free tier has a DAILY request
        # quota, so a quota-exhausted day should not blank out weather for
        # all 47 counties -- fall back to the last successful batch instead.
        self._last_good: dict[str, dict[str, Any]] | None = None
        self._last_good_time: float = 0.0
        self._load_last_good_from_disk()


    def _load_last_good_from_disk(self) -> None:
        """On startup, load the last-known-good weather snapshot from disk
        (if one exists) so a server restart does not present a fresh blank
        slate before the first live fetch of this session succeeds."""
        try:
            if not LAST_GOOD_CACHE_FILE.exists():
                return
            with open(LAST_GOOD_CACHE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            data = payload.get("data")
            timestamp = payload.get("timestamp")
            if isinstance(data, dict) and isinstance(timestamp, (int, float)):
                self._last_good = data
                self._last_good_time = timestamp
                logger.info(
                    "ERA5/Open-Meteo: loaded last-known-good weather from disk (%d counties, saved at %s).",
                    len(data), timestamp,
                )
        except Exception as exc:
            # Defensive: a missing/corrupt cache file must never prevent
            # startup or be treated as a hard error -- just start cold,
            # same as if no prior data had ever been fetched.
            logger.warning("ERA5/Open-Meteo: could not load on-disk last-good cache: %s", exc)

    def _persist_last_good_to_disk(self) -> None:
        """Write the current last-known-good snapshot to disk so it survives
        a server restart. Writes to a temp file then renames, so a crash
        mid-write can never leave a corrupt cache file behind."""
        try:
            LAST_GOOD_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = LAST_GOOD_CACHE_FILE.with_suffix(".json.tmp")
            payload = {"timestamp": self._last_good_time, "data": self._last_good}
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp_path, LAST_GOOD_CACHE_FILE)
        except Exception as exc:
            # Defensive: failing to persist to disk must never break the
            # live request in progress -- the in-memory fallback still works.
            logger.warning("ERA5/Open-Meteo: could not persist last-good cache to disk: %s", exc)

    @property
    def provider_name(self) -> str:
        return "ERA5-OpenMeteo"

    def connect(self) -> ConnectorResult:
        url = f"{OPEN_METEO_URL}?latitude=-1.286389&longitude=36.817223&current=temperature_2m"
        ok, text = _curl_get(url, min(self.config.timeout, 15))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Unable to reach Open-Meteo: {text}",
            )

        try:
            data = json.loads(text)

        except ValueError as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Open-Meteo returned an invalid response: {exc}",
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

        def _stale_fallback(reason: str) -> ConnectorResult | None:
            if self._last_good:
                age_min = (now - self._last_good_time) / 60
                logger.warning(
                    "ERA5/Open-Meteo fetch failed (%s); serving last-known-good weather from %.0f min ago.",
                    reason, age_min,
                )
                return ConnectorResult.ok(
                    provider=self.provider_name,
                    operation="search",
                    data=dict(self._last_good),
                    metadata={"cached": True, "stale_fallback": True, "reason": reason},
                )
            return None

        try:
            counties = gpd.read_file(COUNTIES_GEOJSON)

        except Exception as exc:
            fallback = _stale_fallback(f"Failed to load county boundaries: {exc}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Failed to load county boundaries: {exc}",
            )

        names: list[str] = []
        lats: list[str] = []
        lons: list[str] = []

        for _, row in counties.iterrows():
            name = row.get("COUNTY") or row.get("NAME") or row.get("name")

            if not name:
                continue

            centroid = row.geometry.centroid
            names.append(name)
            lats.append(str(round(centroid.y, 4)))
            lons.append(str(round(centroid.x, 4)))

        lat_param = ",".join(lats)
        lon_param = ",".join(lons)

        url = (
            f"{OPEN_METEO_URL}?latitude={lat_param}&longitude={lon_param}"
            "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,surface_pressure"
            "&timezone=auto"
        )

        ok, text = _curl_get(url, min(self.config.timeout, 30))

        if not ok:
            fallback = _stale_fallback(f"Unable to reach Open-Meteo: {text}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Unable to reach Open-Meteo: {text}",
            )

        try:
            data = json.loads(text)

        except ValueError as exc:
            fallback = _stale_fallback(f"Open-Meteo returned an invalid response: {exc}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Open-Meteo returned an invalid response: {exc}",
            )

        # Open-Meteo signals errors (rate limits, bad requests, etc.) as a
        # single JSON object with "error": true -- this must be checked
        # BEFORE the isinstance(data, list) wrap below, or the error body
        # gets silently misread as "1 valid county's worth of data".
        if isinstance(data, dict) and data.get("error"):
            reason = data.get("reason", "Unknown Open-Meteo error")
            fallback = _stale_fallback(f"Open-Meteo error: {reason}")
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Open-Meteo error: {reason}",
            )

        if not isinstance(data, list):
            data = [data]

        if len(data) != len(names):
            fallback = _stale_fallback(
                f"Mismatch: {len(names)} counties requested, {len(data)} results returned."
            )
            if fallback:
                return fallback
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Mismatch: {len(names)} counties requested, {len(data)} results returned.",
            )

        results: dict[str, dict[str, Any]] = {}

        for name, entry in zip(names, data):
            current = entry.get("current", {})
            results[name] = {
                "temperature_c": current.get("temperature_2m"),
                "humidity_pct": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "pressure_hpa": current.get("surface_pressure"),
            }

        self._cache = results
        self._cache_time = now
        self._last_good = dict(results)
        self._last_good_time = now
        self._persist_last_good_to_disk()

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
            error="ERA5-OpenMeteo does not support per-product downloads; use search() instead.",
        )


def build_era5_connector() -> ERA5Connector:
    """Factory: builds an ERA5Connector (Open-Meteo backed)."""

    config = ConnectorConfig(
        connector_id="era5_openmeteo",
        provider="Open-Meteo",
        enabled=True,
        base_url=OPEN_METEO_URL,
        timeout=settings.http_timeout,
        credentials={},
    )
    return ERA5Connector(config)
