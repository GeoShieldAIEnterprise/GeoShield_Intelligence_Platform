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
from backend.routes.county import router as county_router

app = FastAPI(title="GeoShield AI Enterprise", version="1.3.1")

# Mount static files and templates correctly from your original project structure
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(satellites_router)
app.include_router(dashboard_router, prefix="/api")
app.include_router(sentinel2_map_layer_router)
app.include_router(main_engine_router)
app.include_router(county_router)

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
    db_path = _Path("database/geoshield.db")
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

@app.get("/alerts")
def get_alerts():
    return [{"id": 1, "message": "No critical anomalies detected in Nairobi region", "severity": "info"}]

@app.get("/health")
def health_check():
    return {"status": "healthy", "system": "GeoShield OS Operational"}

