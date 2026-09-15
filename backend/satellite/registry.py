"""
GeoShield AI Enterprise
Satellite Registry

Central registry for all satellite and Earth-observation
data providers used by GeoShield.

Sentinel-2 is currently active.
Other providers are registered as planned/inactive
until their connectors are implemented.
"""

from __future__ import annotations

from typing import Any


SATELLITE_REGISTRY: dict[str, dict[str, Any]] = {

    "sentinel2": {
        "id": "sentinel2",
        "name": "Sentinel-2",
        "provider": "Copernicus Data Space",
        "category": "Optical Multispectral",
        "status": "active",
        "description": (
            "Multispectral Earth observation imagery for "
            "vegetation, agriculture, fire and "
            "environmental intelligence."
        ),
        "capabilities": [
            "True Color",
            "NDVI",
            "NDWI",
            "NBR",
            "Agriculture",
            "Fire Analysis",
            "Change Detection",
        ],
        "endpoint": "/sentinel2",
        "how_it_works": (
            "Sentinel-2 carries a multispectral optical camera "
            "(13 bands, from visible light to shortwave infrared) "
            "that images the Earth's surface much like a very "
            "advanced photograph. Different band combinations reveal "
            "vegetation health, water, burn scars, and more."
        ),
        "update_cadence": "Revisits each location every ~5 days (10 days per single satellite; two satellites in the constellation)",
        "external_url": "https://dataspace.copernicus.eu/explore-data/data-collections/sentinel-data/sentinel-2",
    },

    "sentinel1": {
        "id": "sentinel1",
        "name": "Sentinel-1",
        "provider": "Copernicus Data Space",
        "category": "SAR Radar",
        "status": "active",
        "description": (
            "Synthetic Aperture Radar imagery for "
            "flood mapping, surface monitoring and "
            "all-weather Earth observation."
        ),
        "capabilities": [
            "Flood Detection",
            "Surface Monitoring",
            "Change Detection",
            "SAR Analysis",
        ],
        "endpoint": "/sentinel1",
        "how_it_works": (
            "Sentinel-1 sends its own radar pulses at the ground and "
            "measures what bounces back (Synthetic Aperture Radar), "
            "rather than relying on sunlight. This means it can see "
            "through clouds and at night. Water surfaces reflect radar "
            "very differently from land, making flooded areas stand "
            "out distinctly."
        ),
        "update_cadence": "Revisits each location every ~6-12 days",
        "external_url": "https://dataspace.copernicus.eu/explore-data/data-collections/sentinel-data/sentinel-1",
    },

    "viirs": {
        "id": "viirs",
        "name": "VIIRS",
        "provider": "NASA / NOAA",
        "category": "Thermal / Environmental",
        "status": "planned",
        "description": (
            "Near-real-time environmental observations "
            "for fire, thermal anomalies and atmospheric monitoring."
        ),
        "capabilities": [
            "Fire Hotspots",
            "Thermal Anomalies",
            "Nighttime Lights",
            "Environmental Monitoring",
        ],
        "endpoint": "/viirs",
        "how_it_works": (
            "VIIRS carries a thermal infrared sensor that detects "
            "unusually hot pixels on the ground -- active fires burn "
            "far hotter than their surroundings, so they show up as a "
            "distinct thermal signature the sensor can flag "
            "automatically (via NASA's FIRMS active-fire product)."
        ),
        "update_cadence": "Near-real-time, multiple passes per day",
        "external_url": "https://firms.modaps.eosdis.nasa.gov/",
    },

    "gpm": {
        "id": "gpm",
        "name": "GPM",
        "provider": "NASA",
        "category": "Precipitation",
        "status": "planned",
        "description": (
            "Global precipitation observations for "
            "rainfall monitoring and flood intelligence."
        ),
        "capabilities": [
            "Rainfall",
            "Precipitation",
            "Flood Intelligence",
            "Storm Monitoring",
        ],
        "endpoint": "/gpm",
        "how_it_works": (
            "GPM is a constellation of satellites whose microwave and "
            "infrared sensors estimate rainfall rates by sensing "
            "precipitation particles in clouds, even where no ground "
            "rain gauges exist. IMERG combines all these satellites "
            "into a single, frequently-updated global rainfall map."
        ),
        "update_cadence": "New estimates roughly every 30 minutes (Early Run)",
        "external_url": "https://gpm.nasa.gov/data/imerg",
    },

    "era5": {
        "id": "era5",
        "name": "ERA5",
        "provider": "ECMWF / Copernicus",
        "category": "Climate / Weather",
        "status": "planned",
        "description": (
            "Global atmospheric reanalysis data for "
            "weather, climate and environmental intelligence."
        ),
        "capabilities": [
            "Temperature",
            "Wind",
            "Pressure",
            "Humidity",
            "Climate Analysis",
        ],
        "endpoint": "/era5",
        "how_it_works": (
            "ERA5 isn't a single satellite -- it's a reanalysis: "
            "decades of real observations (from many satellites, "
            "weather stations and balloons) fed through a physics "
            "model to produce a consistent, gap-free record of the "
            "atmosphere over time and space."
        ),
        "update_cadence": "Updated within ~5 days of real time",
        "external_url": "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels",
    },
}


def get_all_satellites() -> list[dict[str, Any]]:
    """Return every registered satellite provider."""

    from core.engines.main_engine import main_engine

    satellites = [dict(s) for s in SATELLITE_REGISTRY.values()]
    viirs_connector = main_engine.connectors.get("VIIRS-FIRMS")
    gpm_connector = main_engine.connectors.get("GPM-IMERG")
    era5_connector = main_engine.connectors.get("ERA5-OpenMeteo")

    for s in satellites:
        if s["id"] == "viirs" and viirs_connector is not None and viirs_connector.is_enabled():
            s["status"] = "active"

        if s["id"] == "gpm" and gpm_connector is not None and gpm_connector.is_enabled():
            s["status"] = "active"

        if s["id"] == "era5" and era5_connector is not None and era5_connector.is_enabled():
            s["status"] = "active"

        if s["id"] in ("viirs", "gpm", "era5"):
            live_status = main_engine.get_satellite_live_status(s["id"])

            if live_status:
                s["live_health"] = {
                    "mode": live_status.get("mode"),
                    "checked_at": live_status.get("checked_at"),
                    "summary": (
                        f"{live_status.get('count', 0)} hotspots detected" if s["id"] == "viirs"
                        else f"{len(live_status.get('counties', {}))} counties covered"
                    ),
                }
            else:
                s["live_health"] = None

    return satellites


def get_active_satellites() -> list[dict[str, Any]]:
    """Return only currently active satellite providers."""

    return [
        satellite
        for satellite in get_all_satellites()
        if satellite["status"] == "active"
    ]


def get_satellite(satellite_id: str) -> dict[str, Any] | None:
    """Return one satellite by ID."""

    return SATELLITE_REGISTRY.get(satellite_id)


__all__ = [
    "SATELLITE_REGISTRY",
    "get_all_satellites",
    "get_active_satellites",
    "get_satellite",
]