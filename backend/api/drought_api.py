from __future__ import annotations
from fastapi import APIRouter, Query
from backend.disaster.drought_engine import drought_engine

router = APIRouter(prefix="/api/drought", tags=["drought"])

@router.get("/live")
def live_drought():
    return drought_engine.analyse()

@router.get("/summary")
def drought_summary(county: str = Query(default=None)):
    return drought_engine.get_summary(county=county)
