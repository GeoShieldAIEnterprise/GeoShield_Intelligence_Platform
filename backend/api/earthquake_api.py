from __future__ import annotations
from fastapi import APIRouter, Query
from backend.disaster.earthquake_engine import earthquake_engine

router = APIRouter(prefix="/api/earthquake", tags=["earthquake"])

@router.get("/live")
def live_earthquakes(
    period: str = Query(default="day"),
    min_magnitude: float = Query(default=4.0),
):
    return earthquake_engine.analyse(period=period, min_magnitude=min_magnitude)
