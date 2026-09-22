from __future__ import annotations
from fastapi import APIRouter, Query
from backend.disaster.flood_engine import flood_engine

router = APIRouter(prefix="/api/flood", tags=["flood"])

@router.get("/live")
def live_flood():
    return flood_engine.analyse()

@router.get("/summary")
def flood_summary(county: str = Query(default=None)):
    return flood_engine.get_summary(county=county)
