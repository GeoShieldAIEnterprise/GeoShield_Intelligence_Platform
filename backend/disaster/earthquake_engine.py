"""
GeoShield Earthquake Intelligence Engine

Fetches live earthquakes via the Main Engine's USGS connector,
enriches each with county/road context and live WorldPop population
exposure, scores risk, and attaches a decision recommendation --
mirroring FireIntelligenceEngine's pipeline shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.spatial.data_manager import GeoDataManager
from core.decision_engine import DecisionEngine
from core.engines.main_engine import main_engine
from core.event_enrichment import EventEnrichmentEngine
from core.risk_engine import RiskEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPOSURE_RADIUS_KM = 50.0


class EarthquakeIntelligenceEngine:
    """Main earthquake intelligence processing engine."""

    def __init__(self) -> None:
        self.data_manager = GeoDataManager()

        self.data_manager.load_layer(
            "counties",
            str(PROJECT_ROOT / "data" / "boundaries" / "Kenya_county.shp"),
        )
        try:
            self.data_manager.load_layer(
                "roads",
                str(PROJECT_ROOT / "data" / "roads" / "ken_roads.shp"),
            )
        except FileNotFoundError as exc:
            print(f"[EarthquakeEngine] WARNING: roads layer unavailable ({exc}); road enrichment will be skipped.")

        self.enrichment = EventEnrichmentEngine(self.data_manager)
        self.risk = RiskEngine()
        self.decision = DecisionEngine()

    KENYA_BBOX = (33.5, -5.0, 42.0, 5.5)  # west, south, east, north -- same box used by VIIRS/FIRMS

    def analyse(
        self,
        period: str = "day",
        min_magnitude: float | None = 4.0,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> list[dict[str, Any]]:

        if bbox is None:
            bbox = self.KENYA_BBOX

        feed = main_engine.get_earthquakes(period=period, min_magnitude=min_magnitude)
        events = feed.get("events", [])

        if bbox is not None:
            west, south, east, north = bbox
            events = [
                e for e in events
                if west <= e["longitude"] <= east and south <= e["latitude"] <= north
            ]

        enriched: list[dict[str, Any]] = []

        for event in events:
            location = self.enrichment.enrich(event["longitude"], event["latitude"])

            exposure = main_engine.get_population_exposure(
                latitude=event["latitude"],
                longitude=event["longitude"],
                radius_km=EXPOSURE_RADIUS_KM,
            )

            event_with_population = {
                **event,
                "population_exposed": exposure.get("population"),
                "population_mode": exposure.get("mode"),
                "population_year": exposure.get("year"),
            }

            risk = self.risk.calculate_earthquake_risk(event_with_population)
            decision = self.decision.recommend_earthquake(risk)

            enriched.append({
                **event_with_population,
                **location,
                **risk,
                **decision,
            })

        return enriched

    def get_summary(self, county: str | None = None) -> dict[str, Any]:
        """Called by MainEngine.get_hazard_summary('earthquake', county=...)."""

        events = self.analyse(period="day", min_magnitude=4.0)

        if county:
            events = [e for e in events if e.get("county") == county]

        severity_rank = {"Low": 0, "Moderate": 1, "High": 2, "Extreme": 3}
        risk_level = max((e["severity"] for e in events), default="Low", key=lambda s: severity_rank[s])

        return {
            "hazard": "earthquake",
            "county": county or "All 47 Counties",
            "status": "monitored",
            "satellites": ["USGS-Seismic", "WorldPop"],
            "risk_level": risk_level,
            "event_count": len(events),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


earthquake_engine = EarthquakeIntelligenceEngine()
