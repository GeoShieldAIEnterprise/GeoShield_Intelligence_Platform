"""GeoShield AI Enterprise -- General Storage & Sentinel-2 Ingestion Service (Heavy Mock Simulation)"""
from __future__ import annotations
import asyncio, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import httpx
from PIL import Image, ImageDraw

GEOSHIELD_STORAGE_ROOT = Path(os.getenv("GEOSHIELD_STORAGE_ROOT", "D:\\GeoShield_Storage"))
STORAGE_ROOT = GEOSHIELD_STORAGE_ROOT / "sentinel2"
TILES_DIR = STORAGE_ROOT / "tiles"
INDEX_PATH = STORAGE_ROOT / "index.json"

COPERNICUS_LIVE = os.getenv("COPERNICUS_LIVE", "false").lower() == "true"
POLL_INTERVAL_HOURS = float(os.getenv("SENTINEL2_POLL_INTERVAL_HOURS", "4"))
POLL_BBOX = os.getenv("SENTINEL2_POLL_BBOX", "33.491,-4.730,41.909,5.516")
POLL_MAX_CLOUD_COVER = float(os.getenv("SENTINEL2_POLL_MAX_CLOUD_COVER", "30"))
POLL_LOOKBACK_DAYS = int(os.getenv("SENTINEL2_POLL_LOOKBACK_DAYS", "10"))
POLL_SEARCH_LIMIT = int(os.getenv("SENTINEL2_POLL_SEARCH_LIMIT", "100"))
COPERNICUS_STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"
REQUEST_TIMEOUT_SECONDS = 60
TILE_ID_PATTERN = re.compile(r"_T(\d{2}[A-Z]{3})_")
MOCK_TILE_IDS = ["T37MBU", "T37MCU", "T36MYE", "T37MDU"]

def _ensure_dirs() -> None:
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text(json.dumps({"tiles": {}}, indent=2))

def _extract_tile_id(scene_id: str) -> str:
    match = TILE_ID_PATTERN.search(scene_id)
    return f"T{match.group(1)}" if match else "UNKNOWN"

def _read_index() -> dict[str, Any]:
    _ensure_dirs()
    return json.loads(INDEX_PATH.read_text())

def _write_index(index: dict[str, Any]) -> None:
    INDEX_PATH.write_text(json.dumps(index, indent=2))

def list_tiles() -> list[dict[str, Any]]:
    index = _read_index()
    summary = []
    for tile_id, data in index["tiles"].items():
        scenes = data.get("scenes", [])
        current = next((s for s in scenes if s.get("status") == "current"), None)
        summary.append({"tile_id": tile_id, "current": current, "scene_count": len(scenes)})
    return summary

def get_tile_current(tile_id: str) -> dict[str, Any] | None:
    index = _read_index()
    tile = index["tiles"].get(tile_id)
    if not tile:
        return None
    return next((s for s in tile["scenes"] if s.get("status") == "current"), None)

def get_tile_history(tile_id: str) -> list[dict[str, Any]]:
    index = _read_index()
    tile = index["tiles"].get(tile_id)
    if not tile:
        return []
    return [s for s in tile["scenes"] if s.get("status") != "current"]

async def _find_latest_per_tile() -> dict[str, dict[str, Any]]:
    if not COPERNICUS_LIVE:
        return _mock_latest_per_tile()
    try:
        return await _live_latest_per_tile()
    except httpx.HTTPError as exc:
        print(f"Sentinel-2 ingest: live search failed: {exc}")
        return {}

def _mock_latest_per_tile() -> dict[str, dict[str, Any]]:
    today = datetime.now(timezone.utc)
    result = {}
    for tile_id in MOCK_TILE_IDS:
        scene_id = f"S2A_MSIL2A_{today.strftime('%Y%m%dT%H%M%S')}_{tile_id}_MOCK"
        result[tile_id] = {
            "id": scene_id,
            "date": today.date().isoformat(),
            "cloud_cover": 8.5,
            "assets": {"visual": {"href": None}, "B04": {"href": None}, "B08": {"href": None}}
        }
    return result

async def _live_latest_per_tile() -> dict[str, dict[str, Any]]:
    bbox_values = [float(v) for v in POLL_BBOX.split(",")]
    now = datetime.now(timezone.utc)
    start = now.fromordinal(now.toordinal() - POLL_LOOKBACK_DAYS)
    body = {
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox_values,
        "datetime": f"{start.isoformat()}/{now.isoformat()}",
        "limit": POLL_SEARCH_LIMIT,
        "sortby": [{"field": "properties.datetime", "direction": "desc"}],
        "query": {"eo:cloud_cover": {"lte": POLL_MAX_CLOUD_COVER}}
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(COPERNICUS_STAC_URL, json=body)
        response.raise_for_status()
        payload = response.json()
    
    features = payload.get("features", [])
    latest_per_tile: dict[str, dict[str, Any]] = {}
    for feature in features:
        scene_id = feature.get("id", "unknown")
        tile_id = _extract_tile_id(scene_id)
        if tile_id == "UNKNOWN" or tile_id in latest_per_tile:
            continue
        latest_per_tile[tile_id] = {
            "id": scene_id,
            "date": feature.get("properties", {}).get("datetime", "")[:10],
            "cloud_cover": feature.get("properties", {}).get("eo:cloud_cover", 0.0),
            "assets": feature.get("assets", {})
        }
    return latest_per_tile

async def _download_rasters(scene: dict[str, Any], dest_dir: Path) -> dict[str, str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    assets = scene.get("assets", {})
    downloaded_files = {}
    
    target_keys = [k for k in ["visual", "B04", "B08", "TCI"] if k in assets]
    
    if not COPERNICUS_LIVE:
        # Generate heavy mock raster files (e.g., 125MB per band file to scale up storage rapidly)
        simulated_size_bytes = 125 * 1024 * 1024  
        for key in ["B04", "B08", "visual"]:
            out_path = dest_dir / f"{key}.tif"
            out_path.write_bytes(b"\x00" * simulated_size_bytes)
            downloaded_files[key] = str(out_path)
        return downloaded_files

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        for key in target_keys:
            href = assets[key].get("href")
            if not href:
                continue
            out_path = dest_dir / f"{key}.tif"
            try:
                response = await client.get(href)
                response.raise_for_status()
                out_path.write_bytes(response.content)
                downloaded_files[key] = str(out_path)
            except httpx.HTTPError:
                pass
                
    return downloaded_files

async def _ingest_tile(index: dict[str, Any], tile_id: str, latest: dict[str, Any]) -> bool:
    tile = index["tiles"].setdefault(tile_id, {"scenes": []})
    current = next((s for s in tile["scenes"] if s.get("status") == "current"), None)
    if current is not None and current["id"] == latest["id"]:
        return False
    
    now_iso = datetime.now(timezone.utc).isoformat()
    tile_dir = TILES_DIR / tile_id
    current_dir = tile_dir / "current"
    archive_dir = tile_dir / "archive"
    
    if current is not None:
        outgoing_dir = archive_dir / current["id"]
        outgoing_dir.mkdir(parents=True, exist_ok=True)
        if current_dir.exists():
            for f in current_dir.glob("*"):
                f.rename(outgoing_dir / f.name)
        current["status"] = "archived"
        current["archived_at"] = now_iso
        
    raster_paths = await _download_rasters(latest, current_dir)
    tile["scenes"].append({
        "id": latest["id"],
        "date": latest["date"],
        "cloud_cover": latest["cloud_cover"],
        "status": "current",
        "ingested_at": now_iso,
        "raster_paths": raster_paths,
        "imagery_deleted": False
    })
    return True

async def run_ingest_cycle() -> dict[str, Any]:
    _ensure_dirs()
    latest_per_tile = await _find_latest_per_tile()
    if not latest_per_tile:
        return {"updated": False, "reason": "no tiles found", "tiles_updated": []}
    index = _read_index()
    updated_tiles = []
    for tile_id, latest in latest_per_tile.items():
        if await _ingest_tile(index, tile_id, latest):
            updated_tiles.append(tile_id)
    _write_index(index)
    return {"updated": len(updated_tiles) > 0, "tiles_checked": list(latest_per_tile.keys()), "tiles_updated": updated_tiles}

async def sentinel2_polling_loop() -> None:
    _ensure_dirs()
    while True:
        try:
            await run_ingest_cycle()
        except Exception as exc:
            print(f"Sentinel-2 ingest error: {exc}")
        await asyncio.sleep(POLL_INTERVAL_HOURS * 3600)
