"""
GeoShield River Discharge Connector (GloFAS via Open-Meteo)

Live per-county river discharge (m3/s) via Open-Meteo's Flood API
(flood-api.open-meteo.com), backed by the Global Flood Awareness
System (GloFAS v4). Unlike local rainfall, river discharge reflects
water actually flowing through a river NOW -- including water that
fell hundreds of km upstream days earlier (e.g. Aberdares/Mt Kenya
rainfall reaching the Tana River basin downstream). This is the
signal Kenya Met's own flood bulletins are built on.

Query coordinates come from data/county_river_lookup.json, generated
once offline from HydroRIVERS (HydroSHEDS) -- for each county, a real
point on its largest river's actual channel, plus that river's total
upstream drainage area (UPLAND_SKM, used as a drainage-risk proxy)
and long-term reference discharge (DIS_AV_CMS). County centroids do
NOT work for this: rivers are linear features, and a county's
geometric center can easily land kilometers from any actual channel,
returning 0 m3/s even for major rivers (confirmed during development
-- Tana River county centroid, and several manually-guessed points
near Garissa, all returned 0 despite the Tana carrying real flow).

Same request pattern as ERA5Connector (Open-Meteo, keyless, curl.exe,
comma-separated multi-county coordinates in one request).
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from core.config import settings
from .base_connector import BaseConnector
from .connector_config import ConnectorConfig
from .connector_result import ConnectorResult

FLOOD_API_URL = "https://flood-api.open-meteo.com/v1/flood"
COUNTY_RIVER_LOOKUP = Path("data/county_river_lookup.json")
CACHE_MINUTES = 180  # river discharge changes slowly; daily-resolution data, no need to refetch often


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


class GloFASFloodConnector(BaseConnector):
    """Live river discharge connector via Open-Meteo's Flood API (GloFAS)."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._cache: dict[str, Any] | None = None
        self._cache_time: float = 0.0

    @property
    def provider_name(self) -> str:
        return "GloFAS-OpenMeteo"

    def _load_river_lookup(self) -> dict[str, Any]:
        with open(COUNTY_RIVER_LOOKUP, "r", encoding="utf-8") as f:
            return json.load(f)

    def connect(self) -> ConnectorResult:
        url = f"{FLOOD_API_URL}?latitude=-1.286389&longitude=36.817223&daily=river_discharge&forecast_days=1&past_days=14"
        ok, text = _curl_get(url, min(self.config.timeout, 15))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Unable to reach Open-Meteo Flood API: {text}",
            )

        try:
            data = json.loads(text)

        except ValueError as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Open-Meteo Flood API returned an invalid response: {exc}",
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

        try:
            river_lookup = self._load_river_lookup()

        except Exception as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Failed to load county_river_lookup.json: {exc}",
            )

        # Only query counties that actually intersect a major river --
        # counties with none genuinely have no major-river discharge risk.
        queryable = {
            name: info for name, info in river_lookup.items()
            if info.get("has_major_river") and info.get("representative_lat") is not None
        }

        names = list(queryable.keys())
        lats = [str(queryable[n]["representative_lat"]) for n in names]
        lons = [str(queryable[n]["representative_lon"]) for n in names]

        results: dict[str, dict[str, Any]] = {}

        # No-river counties get a clear, honest null entry rather than being
        # silently absent from the response.
        for name, info in river_lookup.items():
            if name not in queryable:
                results[name] = {
                    "discharge_m3s": None,
                    "baseline_m3s": None,
                    "anomaly_ratio": None,
                    "upland_skm": info.get("upland_skm"),
                    "reference_discharge_cms": info.get("reference_discharge_cms"),
                    "has_major_river": False,
                }

        if names:
            lat_param = ",".join(lats)
            lon_param = ",".join(lons)

            url = (
                f"{FLOOD_API_URL}?latitude={lat_param}&longitude={lon_param}"
                "&daily=river_discharge&forecast_days=1&past_days=14"
            )

            ok, text = _curl_get(url, min(self.config.timeout, 30))

            if not ok:
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Unable to reach Open-Meteo Flood API: {text}",
                )

            try:
                data = json.loads(text)

            except ValueError as exc:
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Open-Meteo Flood API returned an invalid response: {exc}",
                )

            if not isinstance(data, list):
                data = [data]

            if len(data) != len(names):
                return ConnectorResult.failure(
                    provider=self.provider_name,
                    operation="search",
                    error=f"Mismatch: {len(names)} rivers requested, {len(data)} results returned.",
                )

            for name, entry in zip(names, data):
                daily = entry.get("daily", {})
                discharge = daily.get("river_discharge", [])
                info = queryable[name]

                if not discharge:
                    results[name] = {
                        "discharge_m3s": None,
                        "baseline_m3s": None,
                        "anomaly_ratio": None,
                        "upland_skm": info.get("upland_skm"),
                        "reference_discharge_cms": info.get("reference_discharge_cms"),
                        "has_major_river": True,
                    }
                    continue

                today = discharge[-1]
                past_values = [v for v in discharge[:-1] if v is not None]
                baseline = (sum(past_values) / len(past_values)) if past_values else None

                anomaly_ratio = None
                if baseline is not None and baseline > 0 and today is not None:
                    anomaly_ratio = round(today / baseline, 3)

                results[name] = {
                    "discharge_m3s": today,
                    "baseline_m3s": round(baseline, 2) if baseline is not None else None,
                    "anomaly_ratio": anomaly_ratio,
                    "upland_skm": info.get("upland_skm"),
                    "reference_discharge_cms": info.get("reference_discharge_cms"),
                    "has_major_river": True,
                }

        self._cache = results
        self._cache_time = now

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=results,
            metadata={"cached": False, "county_count": len(results), "rivers_queried": len(names)},
        )

    def download(self, product_id: str) -> ConnectorResult:
        return ConnectorResult.failure(
            provider=self.provider_name,
            operation="download",
            error="GloFAS-OpenMeteo does not support per-product downloads; use search() instead.",
        )


def build_glofas_flood_connector() -> GloFASFloodConnector:
    """Factory: builds a GloFASFloodConnector (Open-Meteo Flood API backed)."""

    config = ConnectorConfig(
        connector_id="glofas_openmeteo",
        provider="Open-Meteo-Flood",
        enabled=True,
        base_url=FLOOD_API_URL,
        timeout=settings.http_timeout,
        credentials={},
    )
    return GloFASFloodConnector(config)
