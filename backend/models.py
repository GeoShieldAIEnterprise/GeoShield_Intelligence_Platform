from sqlalchemy import Column, String, Float, JSON, DateTime
from backend.database import Base
import datetime

class TileModel(Base):
    __tablename__ = "sentinel2_tiles"

    tile_id = Column(String, primary_key=True, index=True)
    current_scene_id = Column(String, nullable=True)
    current_cloud_cover = Column(Float, nullable=True)
    current_path = Column(String, nullable=True)
    history = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
