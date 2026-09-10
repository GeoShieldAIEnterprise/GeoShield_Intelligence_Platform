import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import TileModel

# Official Copernicus Data Space Ecosystem STAC API endpoint
STAC_API_URL = "https://stac.dataspace.copernicus.eu/v1/search"

def fetch_and_store_copernicus_data(bbox: list, tile_id: str):
    """
    Queries the live Copernicus STAC API for a given bounding box [min_lon, min_lat, max_lon, max_lat]
    and updates the PostgreSQL database with the latest Sentinel-2 observation.
    """
    db: Session = SessionLocal()
    
    # Define search window for recent acquisitions (last 10 days to catch the 5-day cycle)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=10)
    datetime_str = f"{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"

    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox,
        "datetime": datetime_str,
        "limit": 5,
        "sortby": [{"field": "properties.datetime", "direction": "desc"}]
    }

    try:
        response = requests.post(STAC_API_URL, json=payload, timeout=15)
        if response.status_code != 200:
            print(f"Error querying Copernicus STAC: {response.text}")
            return

        features = response.json().get("features", [])
        if not features:
            print(f"No recent scenes found for tile {tile_id}")
            return

        # Grab the latest available scene
        latest_scene = features[0]
        scene_id = latest_scene.get("id")
        properties = latest_scene.get("properties", {})
        cloud_cover = properties.get("eo:cloud_cover", 0.0)
        acquisition_time = properties.get("datetime")
        
        # Extract asset download link (e.g., visual RGB or COG asset)
        assets = latest_scene.get("assets", {})
        visual_asset = assets.get("visual", {})
        image_path = visual_asset.get("href", "")

        # Check if tile already exists in PostgreSQL
        existing_tile = db.query(TileModel).filter(TileModel.tile_id == tile_id).first()

        if existing_tile:
            # If a new scene ID is detected, archive the old one into history
            if existing_tile.current_scene_id != scene_id:
                history_entry = {
                    "scene_id": existing_tile.current_scene_id,
                    "cloud_cover": existing_tile.current_cloud_cover,
                    "path": existing_tile.current_path,
                    "updated_at": str(existing_tile.updated_at)
                }
                
                # Append to history JSON list safely
                current_history = list(existing_tile.history) if existing_tile.history else []
                current_history.append(history_entry)
                existing_tile.history = current_history

                # Update with new live scene details
                existing_tile.current_scene_id = scene_id
                existing_tile.current_cloud_cover = cloud_cover
                existing_tile.current_path = image_path
                existing_tile.updated_at = datetime.utcnow()
                
                db.commit()
                print(f"Updated tile {tile_id} with new live scene: {scene_id}")
            else:
                print(f"Tile {tile_id} is already up to date.")
        else:
            # Create a brand new record for this tile
            new_tile = TileModel(
                tile_id=tile_id,
                current_scene_id=scene_id,
                current_cloud_cover=cloud_cover,
                current_path=image_path,
                history=[],
                updated_at=datetime.utcnow()
            )
            db.add(new_tile)
            db.commit()
            print(f"Initialized new tile {tile_id} with live scene: {scene_id}")

    except Exception as e:
        print(f"Failed to fetch live data for {tile_id}: {e}")
    finally:
        db.close()
