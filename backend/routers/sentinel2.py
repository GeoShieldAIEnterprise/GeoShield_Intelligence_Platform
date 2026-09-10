"""GeoShield AI Enterprise -- Sentinel-2 API Router"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from backend.services.sentinel2_ingest import list_tiles, get_tile_current, get_tile_history, run_ingest_cycle

router = APIRouter(prefix="/api/sentinel2", tags=["Sentinel-2 Ingestion"])

@router.get("/tiles")
async def get_tiles():
    return {"tiles": list_tiles()}

@router.get("/tiles/{tile_id}")
async def get_tile_detail(tile_id: str):
    current = get_tile_current(tile_id)
    if not current:
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} not found or has no current scene.")
    history = get_tile_history(tile_id)
    return {"tile_id": tile_id, "current": current, "history": history}

@router.post("/ingest")
async def trigger_ingest():
    result = await run_ingest_cycle()
    return result
