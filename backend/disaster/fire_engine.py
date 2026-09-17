"""
GeoShield Fire Intelligence Engine

Fetches live VIIRS hotspots via the Main Engine's FIRMS connector,
translates FIRMS CSV fields into the shape RiskEngine expects,
enriches each with county/road context, scores fire risk, and
attaches a decision recommendation -- mirroring
EarthquakeIntelligenceEngine's and AgricultureIntelligenceEngine's
pipeline shape.
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


class FireIntelligenceEngine:
    """Main fire intelligence processing engine."""

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
            print(f"[FireEngine] WARNING: roads layer unavailable ({exc}); road enrichment will be skipped.")

        self.enrichment = EventEnrichmentEngine(self.data_manager)
        self.risk = RiskEngine()
        self.decision = DecisionEngine()

    def analyse(self, day_range: int = 1) -> list[dict[str, Any]]:
        feed = main_engine.get_viirs_hotspots(day_range=day_range)
        hotspots = feed.get("hotspots", [])

        enriched: list[dict[str, Any]] = []

        for spot in hotspots:
            try:
                latitude = float(spot["latitude"])
                longitude = float(spot["longitude"])
                brightness = float(spot.get("bright_ti4", spot.get("brightness", 0)))
                frp = float(spot.get("frp", 0))
            except (KeyError, ValueError, TypeError):
                continue  # skip malformed rows rather than crash the whole batch

            fire_record = {
                **spot,
                "latitude": latitude,
                "longitude": longitude,
                "brightness": brightness,
                "frp": frp,
                "confidence": str(spot.get("confidence", "l")),
            }

            location = self.enrichment.enrich(longitude, latitude)
            risk = self.risk.calculate_fire_risk(fire_record)
            decision = self.decision.recommend(risk)

            enriched.append({
                **fire_record,
                **location,
                **risk,
                **decision,
            })

        return enriched

    def get_summary(self, county: str | None = None) -> dict[str, Any]:
        """Called by MainEngine.get_hazard_summary('fire', county=...)."""

        events = self.analyse(day_range=1)

        if county:
            events = [e for e in events if e.get("county") == county]

        severity_rank = {"Low": 0, "Moderate": 1, "High": 2, "Extreme": 3}
        risk_level = max((e["severity"] for e in events), default="Low", key=lambda s: severity_rank[s])

        return {
            "hazard": "fire",
            "county": county or "All 47 Counties",
            "status": "monitored",
            "satellites": ["VIIRS-FIRMS", "ERA5-OpenMeteo"],
            "risk_level": risk_level,
            "event_count": len(events),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


fire_engine = FireIntelligenceEngine()
