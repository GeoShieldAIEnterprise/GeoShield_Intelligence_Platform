from __future__ import annotations
from fastapi import APIRouter, Query
from backend.analytics.analytics_engine import analytics_engine

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/engines")
def engine_health():
    return analytics_engine.get_engine_health()

@router.get("/counties")
def county_analytics(county: str | None = Query(default=None)):
    return analytics_engine.get_county_analytics(county=county)

@router.get("/satellites")
def satellite_analytics():
    return analytics_engine.get_satellite_analytics()

@router.get("/health")
def geoshield_health():
    return analytics_engine.get_geoshield_health()

@router.get("/history")
def history(engine: str | None = Query(default=None), county: str | None = Query(default=None), hours: int = Query(default=24)):
    return analytics_engine.get_history(engine=engine, county=county, hours=hours)
