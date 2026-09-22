from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import os

from backend.database import get_db
import sqlite3
from pathlib import Path as _Path
from backend.models import TileModel
from backend.api.satellites import router as satellites_router
from backend.routes.dashboard import router as dashboard_router
from backend.api.sentinel2_map_layer import router as sentinel2_map_layer_router
from backend.api.main_engine_api import router as main_engine_router
from backend.api.earthquake_api import router as earthquake_router
from backend.disaster.earthquake_engine import earthquake_engine
from backend.api.agriculture_api import router as agriculture_router
from backend.disaster.agriculture_engine import agriculture_engine
from backend.api.drought_api import router as drought_router
from backend.disaster.drought_engine import drought_engine
from backend.api.flood_api import router as flood_router
from backend.disaster.flood_engine import flood_engine
from backend.api.fire_api import router as fire_router
from backend.disaster.fire_engine import fire_engine
from backend.analytics.analytics_engine import analytics_engine
from backend.api.analytics_api import router as analytics_router
import threading
import time
from core.engines.main_engine import main_engine
from backend.routes.county import router as county_router
from engines.alerts.alert_engine import start_alert_orchestrator
from backend.routes.alerts import router as alerts_router
from backend.routes.reports import router as reports_router

app = FastAPI(title="GeoShield AI Enterprise", version="1.3.1")

# Mount static files and templates correctly from your original project structure
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(satellites_router)
app.include_router(dashboard_router, prefix="/api")
app.include_router(sentinel2_map_layer_router)
app.include_router(main_engine_router)
app.include_router(county_router)
app.include_router(earthquake_router)
app.include_router(agriculture_router)
app.include_router(drought_router)
app.include_router(flood_router)
app.include_router(fire_router)
app.include_router(analytics_router)
app.include_router(alerts_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
main_engine.register_engine("earthquake", earthquake_engine)

NDVI_WARMUP_INTERVAL_SECONDS = 170 * 60  # refresh just under the connector's 180-minute cache window

def _ndvi_warmup_loop():
    while True:
        try:
            print("[NDVI Warmup] Refreshing Sentinel-2 NDVI cache...")
            result = main_engine.get_sentinel2_ndvi()
            print(f"[NDVI Warmup] Done -- mode={result.get('mode')}, counties={len(result.get('counties', {}))}")
        except Exception as exc:
            print(f"[NDVI Warmup] Failed: {exc!r}")
        time.sleep(NDVI_WARMUP_INTERVAL_SECONDS)

@app.on_event("startup")
def _start_ndvi_warmup():
    threading.Thread(target=_ndvi_warmup_loop, daemon=True).start()
main_engine.register_engine("agriculture", agriculture_engine)
main_engine.register_engine("drought", drought_engine)
main_engine.register_engine("flood", flood_engine)
main_engine.register_engine("fire", fire_engine)

ANALYTICS_SNAPSHOT_INTERVAL_SECONDS = 5 * 60

def _analytics_snapshot_loop():
    while True:
        try:
            analytics_engine.run_snapshot_cycle()
        except Exception as exc:
            print(f"[Analytics Snapshot] Failed: {exc!r}")
        time.sleep(ANALYTICS_SNAPSHOT_INTERVAL_SECONDS)

@app.on_event("startup")
def _start_analytics_snapshot():
    threading.Thread(target=_analytics_snapshot_loop, daemon=True).start()

HAZARD_WARMUP_INTERVAL_SECONDS = 4 * 60  # refresh just under each engine's 5-minute cache window

def _hazard_cache_warmup_loop():
    while True:
        for name, engine in (
            ("agriculture", agriculture_engine),
            ("drought", drought_engine),
            ("flood", flood_engine),
            ("fire", fire_engine),
        ):
            try:
                records = engine.analyse()
                print(f"[Hazard Warmup] {name}: refreshed, {len(records)} records")
            except Exception as exc:
                print(f"[Hazard Warmup] {name} failed: {exc!r}")
        time.sleep(HAZARD_WARMUP_INTERVAL_SECONDS)

@app.on_event("startup")
def _start_hazard_cache_warmup():
    threading.Thread(target=_hazard_cache_warmup_loop, daemon=True).start()


@app.on_event("startup")
def _start_alert_orchestrator():
    start_alert_orchestrator()


@app.get("/api/latest-tile")
def get_latest_tile(db: Session = Depends(get_db)):
    tile = db.query(TileModel).order_by(TileModel.updated_at.desc()).first()
    if not tile:
        return {"tile_id": "T37MBU", "scene_id": "S2A_MSIL2A_20260904T080451_N0512_R135_T37MBU_20260904T130611", "cloud_cover": 24.48, "updated_at": "2026-09-04 14:14:59"}
    return {
        "tile_id": tile.tile_id,
        "scene_id": tile.current_scene_id,
        "cloud_cover": tile.current_cloud_cover,
        "updated_at": str(tile.updated_at)
    }

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    index_path = "frontend/templates/index.html"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>Frontend template not found at frontend/templates/index.html</h3>"


@app.get("/api/sentinel2/search")
def search_sentinel2(bbox: str = None, cloud_cover: int = 30, limit: int = 20):
    return {"results": [], "status": "success", "bbox": bbox}

@app.get("/resources/{county_name}")
def get_county_resources(county_name: str):
    from core.config import settings as _settings
    db_path = _Path(_settings.data_dir) / "geoshield.db"
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, category, county, latitude, longitude, status, capacity, contact "
        "FROM infrastructure WHERE county = ?",
        (county_name,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/health")
def health_check():
    return {"status": "healthy", "system": "GeoShield OS Operational"}

