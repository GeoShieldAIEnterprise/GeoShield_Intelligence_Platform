"""
GeoShield AI Enterprise -- Main Engine
Single point of coordination for the entire platform.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from core.auth.copernicus import CopernicusAuthManager
from core.auth.exceptions import (
    CopernicusAuthenticationError,
    CopernicusConfigurationError,
    CopernicusNetworkError,
)
from core.connectors.connector_registry import ConnectorRegistry
from core.connectors.firms_connector import build_firms_connector
from core.connectors.gpm_connector import build_gpm_connector
from core.connectors.era5_connector import build_era5_connector

_auth_manager = CopernicusAuthManager()
DB_PATH = Path("database/geoshield.db")
SENTINELHUB_WMS_BASE = "https://sh.dataspace.copernicus.eu/ogc/wms/dc50e71d-6b64-4439-84ef-2e704e48f6f5"

def _build_connector_registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    registry.register(build_firms_connector())
    registry.register(build_gpm_connector())
    registry.register(build_era5_connector())
    return registry


_connector_registry = _build_connector_registry()


class MainEngine:
    """Central coordination point for all GeoShield AI subsystems and satellite feeds."""

    def __init__(self):
        self.registered_engines = {}
        self.connectors = _connector_registry
        self._last_status: dict[str, dict] = {}

    def register_engine(self, name: str, engine_instance: Any):
        self.registered_engines[name] = engine_instance

    def get_live_tile_layer(self, layer: str = "TRUE-COLOR-S2L2A") -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        try:
            token = _auth_manager.get_token()
        except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError) as exc:
            print(f"[MainEngine] Copernicus auth failed: {exc!r}")
            token = None
        
        if token:
            return {
                "mode": "live",
                "kind": "wms",
                "tile_url_template": f"{SENTINELHUB_WMS_BASE}?access_token={token}",
                "wms_layer": layer,
                "checked_at": now,
            }
        return {
            "mode": "mock",
            "kind": "xyz",
            "tile_url_template": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "wms_layer": None,
            "checked_at": now,
        }

    def get_resources(self, county: str | None = None) -> list[dict[str, Any]]:
        if not DB_PATH.exists():
            return []
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if county:
            cursor.execute(
                "SELECT name, category, county, latitude, longitude, status, capacity, contact "
                "FROM infrastructure WHERE county = ?",
                (county,),
            )
        else:
            cursor.execute(
                "SELECT name, category, county, latitude, longitude, status, capacity, contact "
                "FROM infrastructure"
            )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_system_status(self) -> dict[str, Any]:
        tile_status = self.get_live_tile_layer()
        return {
            "status": "healthy",
            "sentinel2_mode": tile_status["mode"],
            "active_engines": list(self.registered_engines.keys()),
            "resources_available": DB_PATH.exists(),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_viirs_hotspots(self, day_range: int = 1) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        connector = self.connectors.get("VIIRS-FIRMS")

        if connector is None or not connector.is_enabled():
            result = {
                "mode": "mock",
                "provider": "VIIRS-FIRMS",
                "hotspots": [],
                "count": 0,
                "checked_at": now,
            }
            self._last_status["viirs"] = result
            return result

        result_obj = connector.search(day_range=day_range)

        if not result_obj.success:
            print(f"[MainEngine] FIRMS search failed: {result_obj.error}")
            result = {
                "mode": "mock",
                "provider": "VIIRS-FIRMS",
                "hotspots": [],
                "count": 0,
                "error": result_obj.error,
                "checked_at": now,
            }
            self._last_status["viirs"] = result
            return result

        result = {
            "mode": "live",
            "provider": "VIIRS-FIRMS",
            "hotspots": result_obj.data,
            "count": result_obj.metadata.get("count", len(result_obj.data)),
            "checked_at": now,
        }
        self._last_status["viirs"] = result
        return result

    def get_gpm_rainfall(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        connector = self.connectors.get("GPM-IMERG")

        if connector is None or not connector.is_enabled():
            result = {
                "mode": "mock",
                "provider": "GPM-IMERG",
                "counties": {},
                "checked_at": now,
            }
            self._last_status["gpm"] = result
            return result

        result_obj = connector.search()

        if not result_obj.success:
            print(f"[MainEngine] GPM search failed: {result_obj.error}")
            result = {
                "mode": "mock",
                "provider": "GPM-IMERG",
                "counties": {},
                "error": result_obj.error,
                "checked_at": now,
            }
            self._last_status["gpm"] = result
            return result

        result = {
            "mode": "live",
            "provider": "GPM-IMERG",
            "counties": result_obj.data,
            "cached": result_obj.metadata.get("cached", False),
            "checked_at": now,
        }
        self._last_status["gpm"] = result
        return result

    def get_era5_weather(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        connector = self.connectors.get("ERA5-OpenMeteo")

        if connector is None or not connector.is_enabled():
            result = {
                "mode": "mock",
                "provider": "ERA5-OpenMeteo",
                "counties": {},
                "checked_at": now,
            }
            self._last_status["era5"] = result
            return result

        result_obj = connector.search()

        if not result_obj.success:
            print(f"[MainEngine] ERA5/Open-Meteo search failed: {result_obj.error}")
            result = {
                "mode": "mock",
                "provider": "ERA5-OpenMeteo",
                "counties": {},
                "error": result_obj.error,
                "checked_at": now,
            }
            self._last_status["era5"] = result
            return result

        result = {
            "mode": "live",
            "provider": "ERA5-OpenMeteo",
            "counties": result_obj.data,
            "cached": result_obj.metadata.get("cached", False),
            "checked_at": now,
        }
        self._last_status["era5"] = result
        return result

    def get_satellite_live_status(self, satellite_id: str) -> dict[str, Any] | None:
        """Return the last-known live status for a satellite without triggering a fresh call."""
        return self._last_status.get(satellite_id)

    def get_hazard_summary(self, hazard: str, county: str | None = None) -> dict[str, Any]:
        if hazard in self.registered_engines:
            return self.registered_engines[hazard].get_summary(county=county)
        
        # Default mock structure mapped to satellite telemetry sources requested
        sources_map = {
            "drought": ["VIIRS", "GPM", "ERA5"],
            "fire": ["VIIRS", "ERA5", "Sentinel-2"],
            "earthquake": ["Seismic-Array", "ERA5"],
            "agriculture": ["VIIRS", "GPM", "ERA5", "Sentinel-2"],
            "flood": ["VIIRS", "GPM", "ERA5"]
        }
        return {
            "hazard": hazard,
            "county": county or "All 47 Counties",
            "status": "monitored",
            "satellites": sources_map.get(hazard, ["Sentinel-2"]),
            "risk_level": "Moderate",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

main_engine = MainEngine()

