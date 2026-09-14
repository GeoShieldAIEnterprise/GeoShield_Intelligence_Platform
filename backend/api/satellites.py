"""
GeoShield AI Enterprise
Satellite Registry API
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.satellite.registry import (
    get_active_satellites,
    get_all_satellites,
    get_satellite,
)


router = APIRouter(
    prefix="/api/satellites",
    tags=["Satellites"],
)


@router.get("")
def satellites():
    """
    Return all satellite providers registered
    with GeoShield.
    """

    satellites = get_all_satellites()

    return {
        "status": "success",
        "count": len(satellites),
        "satellites": satellites,
    }


@router.get("/active")
def active_satellites():
    """
    Return currently active satellite providers.
    """

    satellites = get_active_satellites()

    return {
        "status": "success",
        "count": len(satellites),
        "satellites": satellites,
    }


@router.get("/{satellite_id}")
def satellite(satellite_id: str):
    """
    Return information about one registered satellite.
    """

    result = get_satellite(satellite_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Satellite '{satellite_id}' is not registered.",
        )

    return {
        "status": "success",
        "satellite": result,
    }

