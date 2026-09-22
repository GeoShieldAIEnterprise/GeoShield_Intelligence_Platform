"""
GeoShield Flood Intelligence Engine

Combines live GPM rainfall, ERA5 weather, and Sentinel-2 NDVI per
county via the Main Engine's connectors, scores flood risk (including
flash-flood potential from heat-hardened dry soil), and attaches
recommended actions -- mirroring AgricultureIntelligenceEngine's
pipeline shape.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from core.engines.main_engine import main_engine
from core.risk_engine import RiskEngine


def _recommend_flood(risk: dict[str, Any], flash_watch: bool, flash_reasons: list[str]) -> dict[str, Any]:
    severity = risk.get("severity", "Low")

    actions_map = {
        "Extreme": [
            "Activate county flood emergency response",
            "Pre-position rescue teams near flood-prone wards",
            "Issue evacuation advisory for low-lying areas",
        ],
        "High": [
            "Issue flood advisory to county disaster office",
            "Monitor river levels and drainage capacity closely",
        ],
        "Moderate": [
            "Increase monitoring frequency",
            "Check drainage infrastructure in vulnerable areas",
        ],
        "Low": [
            "Routine monitoring -- no action required",
        ],
    }

    actions = list(actions_map.get(severity, actions_map["Low"]))

    for reason in flash_reasons:
        actions.append(reason)

    return {"recommended_actions": actions, "flash_flood_watch": flash_watch}


CACHE_SECONDS = 300  # 5 minutes -- avoids a full live 47-county fetch on every click


class FloodIntelligenceEngine:
    """Main flood intelligence processing engine."""

    def __init__(self) -> None:
        self.risk = RiskEngine()
        self._cache: list[dict[str, Any]] | None = None
        self._cache_time: float = 0.0

    def analyse(self) -> list[dict[str, Any]]:
        now = time.time()
        if self._cache is not None and (now - self._cache_time) < CACHE_SECONDS:
            return self._cache

        rainfall = main_engine.get_gpm_rainfall()
        weather = main_engine.get_era5_weather()
        ndvi = main_engine.get_sentinel2_ndvi()
        terrain = main_engine.get_terrain()
        river = main_engine.get_river_discharge()

        rainfall_counties = rainfall.get("counties", {})
        weather_counties = weather.get("counties", {})
        ndvi_counties = ndvi.get("counties", {})
        terrain_counties = terrain.get("counties", {})
        river_counties = river.get("counties", {})

        all_counties = set(rainfall_counties.keys()) | set(weather_counties.keys()) | set(ndvi_counties.keys())

        enriched: list[dict[str, Any]] = []

        for county in sorted(all_counties):
            weather_data = weather_counties.get(county, {})
            ndvi_value = ndvi_counties.get(county)
            temperature_c = weather_data.get("temperature_c")

            terrain_data = terrain_counties.get(county, {})
            river_data = river_counties.get(county, {})

            record = {
                "county": county,
                "rainfall_mm": rainfall_counties.get(county),
                "temperature_c": temperature_c,
                "humidity_pct": weather_data.get("humidity_pct"),
                "wind_speed_kmh": weather_data.get("wind_speed_kmh"),
                "ndvi": ndvi_value,
                "elevation_range_m": terrain_data.get("elevation_range_m"),
                "mean_elevation_m": terrain_data.get("mean_elevation_m"),
                "upland_skm": river_data.get("upland_skm"),
                "reference_discharge_cms": river_data.get("reference_discharge_cms"),
                "has_major_river": river_data.get("has_major_river"),
                "discharge_m3s": river_data.get("discharge_m3s"),
                "discharge_anomaly_ratio": river_data.get("anomaly_ratio"),
                "rainfall_mode": rainfall.get("mode"),
                "weather_mode": weather.get("mode"),
                "ndvi_mode": ndvi.get("mode"),
                "terrain_mode": terrain.get("mode"),
            }

            risk = self.risk.calculate_flood_risk(record)

            elevation_range_m = terrain_data.get("elevation_range_m")

            hot_dry_trigger = (
                temperature_c is not None and temperature_c >= 32
                and ndvi_value is not None and ndvi_value <= 0.35
            )

            # Steep terrain sheds rainfall fast -- when meaningful rain is
            # actually falling on steep ground, runoff can outpace drainage
            # capacity in minutes, causing flash flooding even in counties
            # that are not otherwise flood-prone (different mechanism than
            # the hot/dry-soil trigger above, which is a susceptibility
            # signal rather than an active-rain signal).
            steep_rain_trigger = (
                elevation_range_m is not None and elevation_range_m >= 600
                and record.get("rainfall_mm") is not None and record.get("rainfall_mm") >= 15
            )

            flash_watch = hot_dry_trigger or steep_rain_trigger

            flash_reasons = []
            if hot_dry_trigger:
                flash_reasons.append("Flash flood watch: hot, sparse-vegetation soil sheds rainfall fast")
            if steep_rain_trigger:
                flash_reasons.append("Flash flood watch: steep terrain with active rainfall -- fast runoff risk")

            decision = _recommend_flood(risk, flash_watch, flash_reasons)

            enriched.append({
                **record,
                **risk,
                **decision,
            })

        self._cache = enriched
        self._cache_time = now
        return enriched

    def get_summary(self, county: str | None = None) -> dict[str, Any]:
        """Called by MainEngine.get_hazard_summary('flood', county=...)."""

        records = self.analyse()

        if county:
            records = [r for r in records if r.get("county") == county]

        severity_rank = {"Low": 0, "Moderate": 1, "High": 2, "Extreme": 3}
        risk_level = max(
            (r["severity"] for r in records),
            default="Low",
            key=lambda s: severity_rank[s],
        )

        main_engine.submit_engine_output(
            engine="flood", county=county, metric="severity_rank",
            value=float(severity_rank[risk_level]), mode="live",
        )

        return {
            "hazard": "flood",
            "county": county or "All 47 Counties",
            "status": "monitored",
            "satellites": ["GPM-IMERG", "ERA5-OpenMeteo", "Sentinel2-NDVI"],
            "risk_level": risk_level,
            "county_count": len(records),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


flood_engine = FloodIntelligenceEngine()
