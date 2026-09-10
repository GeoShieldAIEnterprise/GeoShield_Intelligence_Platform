"""GeoShield AI Enterprise -- Sentinel-2 Storage API (v2, multi-tile)"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services import sentinel2_ingest
router = APIRouter(prefix="/api/sentinel2/storage", tags=["sentinel2-storage"])
class IngestResult(BaseModel):
    updated: bool
    reason: str | None = None
    tiles_checked: list[str] | None = None
    tiles_updated: list[str] | None = None
@router.get("/tiles")
async def get_tiles():
    return {"tiles": sentinel2_ingest.list_tiles()}
@router.get("/tiles/{tile_id}/current")
async def get_tile_current(tile_id: str):
    scene = sentinel2_ingest.get_tile_current(tile_id)
    if scene is None:
        return {"scene": None, "note": f"No current scene for tile '{tile_id}' yet."}
    return {"tile_id": tile_id, "scene": scene}
@router.get("/tiles/{tile_id}/history")
async def get_tile_history(tile_id: str):
    return {"tile_id": tile_id, "scenes": sentinel2_ingest.get_tile_history(tile_id)}
@router.post("/check-now", response_model=IngestResult)
async def check_now():
    result = await sentinel2_ingest.run_ingest_cycle()
    return IngestResult(**result)
@router.delete("/tiles/{tile_id}/archive/{scene_id}")
async def delete_archived(tile_id: str, scene_id: str):
    deleted = sentinel2_ingest.delete_archived_scene(tile_id, scene_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No archived scene '{scene_id}' found for tile '{tile_id}'.")
    return {"deleted": True, "tile_id": tile_id, "scene_id": scene_id, "note": "Index record kept for reference; only the imagery file was removed."}
