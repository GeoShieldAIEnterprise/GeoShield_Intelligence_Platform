"""
GeoShield Agriculture Intelligence Engine

Combines live GPM rainfall and ERA5 weather (temperature, humidity)
per county via the Main Engine's connectors, scores agricultural/
drought risk, and attaches a decision recommendation -- mirroring
EarthquakeIntelligenceEngine's pipeline shape.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from core.decision_engine import DecisionEngine
from core.engines.main_engine import main_engine
from core.risk_engine import RiskEngine


CACHE_SECONDS = 300  # 5 minutes -- avoids a full live 47-county fetch on every click


class AgricultureIntelligenceEngine:
    """Main agriculture intelligence processing engine."""

    def __init__(self) -> None:
        self.risk = RiskEngine()
        self.decision = DecisionEngine()
        self._cache: list[dict[str, Any]] | None = None
        self._cache_time: float = 0.0

    def analyse(self) -> list[dict[str, Any]]:
        now = time.time()
        if self._cache is not None and (now - self._cache_time) < CACHE_SECONDS:
            return self._cache

        rainfall = main_engine.get_gpm_rainfall()
        weather = main_engine.get_era5_weather()
        ndvi = main_engine.get_sentinel2_ndvi()

        rainfall_counties = rainfall.get("counties", {})
        weather_counties = weather.get("counties", {})
        ndvi_counties = ndvi.get("counties", {})

        all_counties = set(rainfall_counties.keys()) | set(weather_counties.keys()) | set(ndvi_counties.keys())

        enriched: list[dict[str, Any]] = []

        for county in sorted(all_counties):
            weather_data = weather_counties.get(county, {})

            record = {
                "county": county,
                "rainfall_mm": rainfall_counties.get(county),
                "temperature_c": weather_data.get("temperature_c"),
                "humidity_pct": weather_data.get("humidity_pct"),
                "wind_speed_kmh": weather_data.get("wind_speed_kmh"),
                "ndvi": ndvi_counties.get(county),
                "rainfall_mode": rainfall.get("mode"),
                "weather_mode": weather.get("mode"),
                "ndvi_mode": ndvi.get("mode"),
            }

            risk = self.risk.calculate_agriculture_risk(record)
            decision = self.decision.recommend_agriculture(risk)

            enriched.append({
                **record,
                **risk,
                **decision,
            })

        self._cache = enriched
        self._cache_time = now
        return enriched

    def get_summary(self, county: str | None = None) -> dict[str, Any]:
        """Called by MainEngine.get_hazard_summary('agriculture', county=...)."""

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
            engine="agriculture", county=county, metric="severity_rank",
            value=float(severity_rank[risk_level]), mode="live",
        )

        return {
            "hazard": "agriculture",
            "county": county or "All 47 Counties",
            "status": "monitored",
            "satellites": ["GPM-IMERG", "ERA5-OpenMeteo", "Sentinel2-NDVI"],
            "risk_level": risk_level,
            "county_count": len(records),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


agriculture_engine = AgricultureIntelligenceEngine()
