"""
GeoShield AI Enterprise -- Sentinel-2 Search Route
Standalone, modular FastAPI router.
Mock by default; real Copernicus STAC search when COPERNICUS_LIVE=true.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/sentinel2", tags=["sentinel2"])

COPERNICUS_LIVE = os.getenv("COPERNICUS_LIVE", "false").lower() == "true"
COPERNICUS_STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"
MAX_RESULTS = 20
REQUEST_TIMEOUT_SECONDS = 8


class Sentinel2SearchParams(BaseModel):
    bbox: str = Field(..., description="min_lon,min_lat,max_lon,max_lat")
    start_date: date
    end_date: date
    max_cloud_cover: float = Field(30.0, ge=0, le=100)
    limit: int = Field(10, ge=1, le=MAX_RESULTS)

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: str) -> str:
        parts = value.split(",")
        if len(parts) != 4:
            raise ValueError("bbox must have exactly 4 comma-separated values")
        try:
            [float(p) for p in parts]
        except ValueError as exc:
            raise ValueError("bbox values must be numeric") from exc
        return value

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        return end_date


class Sentinel2Scene(BaseModel):
    id: str
    date: str
    cloud_cover: float
    platform: str = "Sentinel-2"
    product_type: str = "MSIL2A"
    thumbnail_url: str | None = None


class Sentinel2SearchResponse(BaseModel):
    scenes: list[Sentinel2Scene]
    count: int
    source: str


@router.get("/search", response_model=Sentinel2SearchResponse)
async def search_sentinel2(
    bbox: str = Query(..., description="min_lon,min_lat,max_lon,max_lat"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    max_cloud_cover: float = Query(30.0, ge=0, le=100),
    limit: int = Query(10, ge=1, le=MAX_RESULTS),
) -> Sentinel2SearchResponse:
    params = Sentinel2SearchParams(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        limit=limit,
    )

    if not COPERNICUS_LIVE:
        return _mock_search(params)

    try:
        return await _live_search(params)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Copernicus request failed: {exc}",
        ) from exc


def _mock_search(params: Sentinel2SearchParams) -> Sentinel2SearchResponse:
    days_span = (params.end_date - params.start_date).days or 1
    count = min(params.limit, 5)

    scenes = [
        Sentinel2Scene(
            id=f"S2A_MSIL2A_MOCK_{i:03d}",
            date=str(
                params.start_date.fromordinal(
                    params.start_date.toordinal()
                    + (days_span * i) // max(count, 1)
                )
            ),
            cloud_cover=round(min(params.max_cloud_cover, 5.0 * (i + 1)), 1),
        )
        for i in range(count)
    ]

    return Sentinel2SearchResponse(scenes=scenes, count=len(scenes), source="mock")


async def _live_search(params: Sentinel2SearchParams) -> Sentinel2SearchResponse:
    bbox_values = [float(v) for v in params.bbox.split(",")]

    body: dict[str, Any] = {
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox_values,
        "datetime": (
            f"{params.start_date.isoformat()}T00:00:00Z/"
            f"{params.end_date.isoformat()}T23:59:59Z"
        ),
        "limit": params.limit,
        "query": {"eo:cloud_cover": {"lte": params.max_cloud_cover}},
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(COPERNICUS_STAC_URL, json=body)
        response.raise_for_status()
        payload = response.json()

    features = payload.get("features", [])[: params.limit]

    scenes = [
        Sentinel2Scene(
            id=feature.get("id", "unknown"),
            date=feature.get("properties", {}).get("datetime", "")[:10],
            cloud_cover=feature.get("properties", {}).get("eo:cloud_cover", 0.0),
            thumbnail_url=feature.get("assets", {}).get("thumbnail", {}).get("href"),
        )
        for feature in features
    ]

    return Sentinel2SearchResponse(scenes=scenes, count=len(scenes), source="copernicus")
