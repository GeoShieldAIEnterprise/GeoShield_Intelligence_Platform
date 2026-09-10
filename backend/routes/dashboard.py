from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
def dashboard():

    return {
        "system_status": "Online",
        "weather": "23°C • Sunny",
        "alerts": 0,
        "ai_risk": 12,
        "fire_risk": "LOW",

        "bottom": {
            "ndvi": 0.61,
            "rainfall": "34 mm",
            "temperature": "23°C",
            "flood_risk": "Low",
            "fire_risk": "Low",
            "population": "54 Million"
        }
    }
