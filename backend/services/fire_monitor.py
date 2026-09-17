import pandas as pd


def check_kenya_fire():

    try:
        df = pd.read_csv("backend/data/kenya_fires.csv")

    except Exception:
        return {
            "status": "inactive",
            "hotspots": []
        }

    hotspots = []

    for _, row in df.iterrows():

        confidence = str(row["confidence"]).lower()

        if confidence in ["h", "high"]:

            hotspots.append({
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "brightness": float(row["bright_ti4"]),
                "frp": float(row["frp"]),
                "confidence": confidence,
                "date": str(row["acq_date"]),
                "time": str(row["acq_time"]),
                "source": "VIIRS-FIRMS",
            })

    if len(hotspots) == 0:
        return {
            "status": "inactive",
            "hotspots": []
        }

    return {
        "status": "active",
        "hotspots": hotspots
    }
