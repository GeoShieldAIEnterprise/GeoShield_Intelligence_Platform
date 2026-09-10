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

_auth_manager = CopernicusAuthManager()
DB_PATH = Path("database/geoshield.db")
SENTINELHUB_WMS_BASE = "https://sh.dataspace.copernicus.eu/ogc/wms"

class MainEngine:
    """Central coordination point for all GeoShield AI subsystems and satellite feeds."""

    def __init__(self):
        self.registered_engines = {}

    def register_engine(self, name: str, engine_instance: Any):
        self.registered_engines[name] = engine_instance

    def get_live_tile_layer(self, layer: str = "TRUE_COLOR") -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        try:
            token = _auth_manager.get_token()
        except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError):
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
