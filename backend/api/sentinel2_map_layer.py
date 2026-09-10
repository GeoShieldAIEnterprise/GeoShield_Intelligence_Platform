"""
GeoShield AI Enterprise -- Sentinel-2 Live Map Layer
Exposes tile-layer configuration for the Main Map, using the existing
CopernicusAuthManager (password-grant OAuth2) for real Sentinel Hub WMS
tiles. Falls back to mock OSM tiles if authentication fails, so the map
never breaks outright.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from core.auth.copernicus import CopernicusAuthManager
from core.auth.exceptions import (
    CopernicusAuthenticationError,
    CopernicusConfigurationError,
    CopernicusNetworkError,
)

router = APIRouter(prefix="/api/sentinel2", tags=["sentinel2-map-layer"])

SENTINELHUB_WMS_BASE = "https://sh.dataspace.copernicus.eu/ogc/wms"
SENTINELHUB_LAYER = os.getenv("SENTINELHUB_LAYER", "TRUE_COLOR")
MOCK_TILE_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

_auth_manager = CopernicusAuthManager()


class TileLayerConfig(BaseModel):
    mode: str
    kind: str
    tile_url_template: str
    wms_layer: str | None = None
    checked_at: str
    note: str


@router.get("/tile-layer", response_model=TileLayerConfig)
async def get_tile_layer() -> TileLayerConfig:
    import time as _time
    _t0 = _time.time()
    print(f"[sentinel2_map_layer] handler ENTERED at {_t0}", flush=True)

    now = datetime.now(timezone.utc).isoformat()

    try:
        print(f"[sentinel2_map_layer] calling get_token()...", flush=True)
        token = _auth_manager.get_token()
        print(f"[sentinel2_map_layer] get_token() returned after {_time.time() - _t0:.2f}s", flush=True)
    except (CopernicusAuthenticationError, CopernicusConfigurationError, CopernicusNetworkError) as e:
        print(f"[sentinel2_map_layer] Copernicus auth failed after {_time.time() - _t0:.2f}s: {type(e).__name__}: {e}", flush=True)
        token = None

    if token:
        tile_url = f"{SENTINELHUB_WMS_BASE}?access_token={token}"
        return TileLayerConfig(
            mode="live",
            kind="wms",
            tile_url_template=tile_url,
            wms_layer=SENTINELHUB_LAYER,
            checked_at=now,
            note="Live Copernicus Data Space Sentinel Hub WMS endpoint (existing CopernicusAuthManager).",
        )

    return TileLayerConfig(
        mode="mock",
        kind="xyz",
        tile_url_template=MOCK_TILE_TEMPLATE,
        wms_layer=None,
        checked_at=now,
        note="Copernicus authentication failed or is not configured -- serving placeholder OSM tiles.",
    )
