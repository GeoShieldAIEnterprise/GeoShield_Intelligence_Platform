from __future__ import annotations
from fastapi import APIRouter, Query
from core.engines.main_engine import main_engine

router = APIRouter(prefix="/api/main-engine", tags=["main-engine"])

@router.get("/status")
def status():
    return main_engine.get_system_status()

@router.get("/tile-layer")
def tile_layer(layer: str = Query(default="TRUE_COLOR")):
    return main_engine.get_live_tile_layer(layer=layer)

@router.get("/resources")
def resources(county: str | None = Query(default=None)):
    return main_engine.get_resources(county=county)

@router.get("/hazard/{hazard}")
def hazard_summary(hazard: str, county: str | None = Query(default=None)):
    return main_engine.get_hazard_summary(hazard=hazard, county=county)
