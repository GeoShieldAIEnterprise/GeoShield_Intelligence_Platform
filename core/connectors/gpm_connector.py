"""
GeoShield GPM/IMERG Connector

Precipitation data via NASA GPM IMERG (Early Run), accessed through
the PPS jsimpsonhttps server. Implements the standard GeoShield
BaseConnector interface.

Uses curl.exe (Windows Schannel) for network access, consistent with
the FIRMS and Copernicus connectors on this machine (OpenSSL 3.0.20
has known SSLEOFError issues against several external HTTPS servers).

Computes real per-county rainfall (mm) by downloading the latest
1-day IMERG GeoTIFF and running zonal statistics against Kenya's
county boundaries. Result is cached for CACHE_MINUTES since IMERG
Early Run itself only updates a few times per hour.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import rasterio
import rasterio.mask

from core.config import settings
from .base_connector import BaseConnector
from .connector_config import ConnectorConfig
from .connector_result import ConnectorResult

PPS_HOST = "https://jsimpsonhttps.pps.eosdis.nasa.gov"
IMERG_DIR = f"{PPS_HOST}/imerg/gis/early/"
IMERG_LIST_URL = f"{PPS_HOST}/text/imerg/gis/early/"
COUNTIES_GEOJSON = Path("frontend/static/data/kenya_counties.geojson")
CACHE_TIF = Path("core/data/cache/imerg_latest.tif")
CACHE_MINUTES = 60


def _curl_get(url: str, auth: str, timeout: float, out_file: Path | None = None) -> tuple[bool, str]:
    """Fetch a URL via curl.exe with HTTP Basic Auth. Returns (success, text_or_error)."""

    cmd = ["curl.exe", "-s", "-u", auth, "--max-time", str(int(timeout))]

    if out_file:
        cmd += ["-o", str(out_file)]

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)

    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"curl failed to run: {exc}"

    if result.returncode != 0:
        return False, f"curl exited with code {result.returncode}: {result.stderr}"

    return True, result.stdout


class GPMConnector(BaseConnector):
    """GPM/IMERG precipitation connector via NASA PPS."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._cache: dict[str, Any] | None = None
        self._cache_time: float = 0.0

    @property
    def provider_name(self) -> str:
        return "GPM-IMERG"

    def _auth_string(self) -> str:
        email = self.config.credentials.get("email", "")
        return f"{email}:{email}"

    def connect(self) -> ConnectorResult:
        email = self.config.credentials.get("email", "")

        if not email:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error="GPM_PPS_EMAIL is not configured.",
            )

        ok, text = _curl_get(IMERG_DIR + "V06/", self._auth_string(), min(self.config.timeout, 15))

        if not ok:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="connect",
                error=f"Unable to reach PPS: {text}",
            )

        return ConnectorResult.ok(provider=self.provider_name, operation="connect", data={"reachable": True})

    def _find_latest_1day_file(self) -> str | None:
        auth = self._auth_string()
        ok, text = _curl_get(IMERG_LIST_URL, auth, min(self.config.timeout, 30))

        if not ok:
            return None

        lines = [line.strip() for line in text.splitlines() if line.strip().endswith(".1day.tif")]

        if not lines:
            return None

        return lines[-1]

    def _compute_zonal_stats(self) -> dict[str, float]:
        counties = gpd.read_file(COUNTIES_GEOJSON)
        results: dict[str, float] = {}

        with rasterio.open(CACHE_TIF) as src:
            for _, row in counties.iterrows():
                name = row.get("COUNTY") or row.get("NAME") or row.get("name")

                if not name:
                    continue

                geom = [row.geometry.__geo_interface__]

                try:
                    out_image, _ = rasterio.mask.mask(src, geom, crop=True)

                except ValueError:
                    results[name] = 0.0
                    continue

                pixels = out_image[0]
                valid = pixels[pixels > 0]
                mean_mm = (float(valid.mean()) / 10.0) if len(valid) else 0.0
                results[name] = round(mean_mm, 2)

        return results

    def search(self, **filters: Any) -> ConnectorResult:
        now = time.time()

        if self._cache is not None and (now - self._cache_time) < (CACHE_MINUTES * 60):
            return ConnectorResult.ok(
                provider=self.provider_name,
                operation="search",
                data=self._cache,
                metadata={"cached": True, "cache_age_seconds": round(now - self._cache_time)},
            )

        email = self.config.credentials.get("email", "")

        if not email:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error="GPM_PPS_EMAIL is not configured.",
            )

        latest_path = self._find_latest_1day_file()

        if not latest_path:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error="Could not find a recent 1-day IMERG file.",
            )

        CACHE_TIF.parent.mkdir(parents=True, exist_ok=True)
        file_url = PPS_HOST + latest_path

        ok, text = _curl_get(file_url, self._auth_string(), min(self.config.timeout, 60), out_file=CACHE_TIF)

        if not ok or not CACHE_TIF.exists() or CACHE_TIF.stat().st_size < 1000:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Failed to download IMERG file: {text}",
            )

        try:
            stats = self._compute_zonal_stats()

        except Exception as exc:
            return ConnectorResult.failure(
                provider=self.provider_name,
                operation="search",
                error=f"Zonal statistics failed: {exc}",
            )

        self._cache = stats
        self._cache_time = now

        return ConnectorResult.ok(
            provider=self.provider_name,
            operation="search",
            data=stats,
            metadata={"cached": False, "source_file": latest_path},
        )

    def download(self, product_id: str) -> ConnectorResult:
        return ConnectorResult.failure(
            provider=self.provider_name,
            operation="download",
            error="GPM-IMERG does not support per-product downloads; use search() instead.",
        )


def build_gpm_connector() -> GPMConnector:
    """Factory: builds a GPMConnector wired to GeoShield settings."""

    config = ConnectorConfig(
        connector_id="gpm_imerg",
        provider="NASA-GPM",
        enabled=bool(settings.gpm_pps_email),
        base_url=PPS_HOST,
        timeout=settings.http_timeout,
        credentials={"email": settings.gpm_pps_email},
    )
    return GPMConnector(config)

