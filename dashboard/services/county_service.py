"""
GeoShield Dashboard County Service

Reads the latest per-county snapshots from analytics_history (written
every 5 minutes by AnalyticsEngine.run_snapshot_cycle) instead of
recomputing live across all engines on every request -- this is what
keeps a county click on the main Dashboard fast: data is at most one
snapshot cycle (5 minutes) old, matching the Analytics page's own
freshness model.
"""

import sqlite3
from pathlib import Path
from core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(settings.data_dir) / "geoshield.db"

RANK_TO_SEVERITY = {0: "Low", 1: "Moderate", 2: "High", 3: "Extreme"}


def _latest_values_for_county(name):
    """One connection, one query: pulls every metric this county needs
    in a single round trip instead of six separate connects."""
    if not DB_PATH.exists():
        return {}

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "SELECT engine, metric, value FROM analytics_history "
        "WHERE county = ? AND id IN ("
        "  SELECT MAX(id) FROM analytics_history "
        "  WHERE county = ? GROUP BY engine, metric"
        ")",
        (name, name),
    )
    rows = cur.fetchall()
    conn.close()

    result = {}
    for engine, metric, value in rows:
        result[(engine, metric)] = value
    return result


def dashboard_summary():
    if not DB_PATH.exists():
        return {"counties": 0}
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT county, value FROM analytics_history "
        "WHERE engine = 'agriculture' AND metric ='severity_rank' "
        "AND id IN (SELECT MAX(id) FROM analytics_history "
        "WHERE engine = 'agriculture' AND metric ='severity_rank' GROUP BY county)"
    )
    rows = cur.fetchall()
    conn.close()
    return {"counties": len(rows)}


def all_counties():
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT county FROM analytics_history "
        "WHERE engine = 'agriculture' AND county IS NOT NULL"
    )
    counties = [row["county"] for row in cur.fetchall()]
    conn.close()
    return [county(c) for c in counties]


def county(name):
    values = _latest_values_for_county(name)

    ndvi = values.get(("agriculture", "ndvi"))
    rainfall = values.get(("agriculture", "rainfall_mm"))
    temperature = values.get(("agriculture", "temperature_c"))

    if ndvi is None and rainfall is None and temperature is None:
        return {"error": "County not found"}

    def risk_label(engine):
        rank = values.get((engine, "severity_rank"))
        if rank is None:
            return "Low"
        return RANK_TO_SEVERITY.get(int(rank), "Low")

    return {
        "County": name,
        "Rainfall_mm": rainfall,
        "Temperature_C": temperature,
        "NDVI": ndvi,
        "Drought_Risk": risk_label("drought"),
        "Flood_Risk": risk_label("flood"),
        "Fire_Risk": risk_label("fire"),
        "Population": "Not yet available -- no live per-county population source wired",
    }
