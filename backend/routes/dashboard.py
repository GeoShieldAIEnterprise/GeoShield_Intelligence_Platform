from fastapi import APIRouter
from core.engines.main_engine import main_engine
from backend.analytics.analytics_engine import analytics_engine

router = APIRouter()


@router.get("/dashboard")
def dashboard(county: str | None = None):
    fire = main_engine.get_hazard_summary("fire", county=county)
    agriculture = main_engine.get_hazard_summary("agriculture", county=county)
    drought = main_engine.get_hazard_summary("drought", county=county)
    flood = main_engine.get_hazard_summary("flood", county=county)

    try:
        from engines.alerts.alert_engine import get_active_alert_count
        alert_count = get_active_alert_count()
    except Exception:
        # Fallback if the orchestrator hasn't started yet or import fails:
        # count hazards currently at High/Extreme for this request only.
        elevated = {"High", "Extreme"}
        alert_count = sum(
            1 for h in (fire, agriculture, drought, flood)
            if h.get("risk_level") in elevated
        )

    overall_risk = "--"
    overall_risk_percent = None
    if county:
        county_analytics = analytics_engine.get_county_analytics(county=county)
        counties = county_analytics.get("counties", [])
        if counties:
            overall_risk = counties[0].get("overall_risk") or "--"
            mean_rank = counties[0].get("mean_rank")
            if mean_rank is not None:
                # SEVERITY_RANK scale is 0 (Low) to 3 (Extreme)
                overall_risk_percent = round((mean_rank / 3) * 100)

    return {
        "system_status": "Online",
        "weather": "Live -- see county detail",
        "alerts": alert_count,
        "overall_risk": overall_risk,
        "overall_risk_percent": overall_risk_percent,
        "fire_risk": fire.get("risk_level", "--"),
        "drought_risk": drought.get("risk_level", "--"),
        "flood_risk": flood.get("risk_level", "--"),
        "agriculture_risk": agriculture.get("risk_level", "--"),

        "bottom": {
            "ndvi": "--",
            "rainfall": "--",
            "temperature": "--",
            "flood_risk": "--",
            "fire_risk": "--",
            "population": "Select a county",
        }
    }
