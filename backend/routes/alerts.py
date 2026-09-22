"""
backend/routes/alerts.py

GET  /api/alerts          -- full historical alert log (with optional
                              county/hazard filters), newest first.
GET  /api/alerts/active   -- only currently-active (Moderate+) alerts.
POST /api/alerts/clear-history -- wipes the historical log only; active
                              alert state is untouched.
"""

from fastapi import APIRouter, Query
from core.engines.main_engine import main_engine
from engines.alerts.alert_engine import get_active_alerts, clear_alert_history

router = APIRouter()


@router.get("/alerts")
def get_alerts(
    limit: int = Query(50, ge=1, le=500),
    county: str | None = None,
    hazard: str | None = None,
):
    """Return the most recent standardized GeoShield alerts, including
    resolved/recovery entries."""
    alerts = main_engine.get_alert_history(limit=limit)

    if county:
        alerts = [a for a in alerts if a.get("county") == county]
    if hazard:
        alerts = [a for a in alerts if a.get("hazard") == hazard]

    return {"count": len(alerts), "alerts": alerts}


@router.get("/alerts/active")
def get_active_alerts_route():
    """Return only currently-active (Moderate+) alerts -- this list
    shrinks as conditions improve, unlike the historical log."""
    alerts = get_active_alerts()
    return {"count": len(alerts), "alerts": alerts}


@router.post("/alerts/clear-history")
def clear_alert_history_route():
    """Permanently clear the historical alert log to free space.
    Does NOT affect currently-active alerts."""
    cleared = clear_alert_history()
    return {"cleared": cleared}
