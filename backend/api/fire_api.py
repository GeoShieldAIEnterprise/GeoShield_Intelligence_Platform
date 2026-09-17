from __future__ import annotations
from fastapi import APIRouter, Query
from backend.disaster.fire_engine import fire_engine

router = APIRouter(prefix="/api/fire", tags=["fire"])

@router.get("/events")
def events(day_range: int = Query(default=1)):
    return fire_engine.analyse(day_range=day_range)

@router.get("/summary")
def summary(county: str | None = Query(default=None)):
    return fire_engine.get_summary(county=county)
