from __future__ import annotations
from fastapi import APIRouter, Query
from backend.disaster.agriculture_engine import agriculture_engine

router = APIRouter(prefix="/api/agriculture", tags=["agriculture"])

@router.get("/live")
def live_agriculture():
    return agriculture_engine.analyse()

@router.get("/summary")
def agriculture_summary(county: str = Query(default=None)):
    return agriculture_engine.get_summary(county=county)
