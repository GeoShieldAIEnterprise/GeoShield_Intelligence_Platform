"""
GeoShield Analytics Engine

Aggregates across all registered engines (Earthquake, Agriculture, Fire)
and MainEngine's connector status to power the Analytics dashboard's
four cards: Engine Health, County Analytics (Overall Risk), Satellite
Analytics, and GeoShield Health -- plus historical time-series queries
backed by the analytics_history table MainEngine writes to.
"""

from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from core.engines.main_engine import main_engine
from core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(settings.data_dir) / "geoshield.db"

SEVERITY_RANK = {"Low": 0, "Moderate": 1, "High": 2, "Extreme": 3}
RANK_TO_SEVERITY = {v: k for k, v in SEVERITY_RANK.items()}

KENYA_COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Embu", "Garissa", "Homa Bay",
    "Isiolo", "Kajiado", "Kakamega", "Keiyo-Marakwet", "Kericho", "Kiambu",
    "Kilifi", "Kirinyaga", "Kisii", "Kisumu", "Kitui", "Kwale", "Laikipia",
    "Lamu", "Machakos", "Makueni", "Mandera", "Marsabit", "Meru", "Migori",
    "Mombasa", "Murang'a", "Nairobi", "Nakuru", "Nandi", "Narok", "Nyamira",
    "Nyandarua", "Nyeri", "Samburu", "Siaya", "Taita Taveta", "Tana River",
    "Tharaka", "Trans Nzoia", "Turkana", "Uasin Gishu", "Vihiga", "Wajir",
    "West Pokot",
]


class AnalyticsEngine:
    """Cross-engine analytics and monitoring layer."""

    def get_engine_health(self) -> dict[str, Any]:
        engines = []
        for name, engine in main_engine.registered_engines.items():
            try:
                summary = engine.get_summary()
                engines.append({
                    "engine": name,
                    "status": summary.get("status", "unknown"),
                    "risk_level": summary.get("risk_level"),
                    "updated_at": summary.get("updated_at"),
                })
            except Exception as exc:
                engines.append({
                    "engine": name,
                    "status": "error",
                    "error": str(exc),
                })
        return {
            "engines": engines,
            "engine_count": len(engines),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_county_analytics(self, county: str | None = None) -> dict[str, Any]:
        if not DB_PATH.exists():
            return {"counties": [], "note": "analytics_history not found"}

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        counties = [county] if county else KENYA_COUNTIES
        results = []

        for c in counties:
            cur.execute(
                "SELECT engine, value FROM analytics_history "
                "WHERE county = ? AND metric = 'severity_rank' AND engine IN ('agriculture','fire','flood','drought') "
                "AND id IN (SELECT MAX(id) FROM analytics_history "
                "WHERE county = ? AND metric = 'severity_rank' GROUP BY engine)",
                (c, c),
            )
            rows = cur.fetchall()

            if not rows:
                results.append({
                    "county": c,
                    "overall_risk": None,
                    "engines_reporting": 0,
                    "note": "no data yet",
                })
                continue

            ranks = [row["value"] for row in rows]
            mean_rank = sum(ranks) / len(ranks)
            overall = RANK_TO_SEVERITY.get(math.floor(mean_rank + 0.5), "Moderate")

            results.append({
                "county": c,
                "overall_risk": overall,
                "mean_rank": round(mean_rank, 2),
                "engines_reporting": len(rows),
            })

        conn.close()
        return {
            "counties": results,
            "county_count": len(results),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_satellite_analytics(self) -> dict[str, Any]:
        satellites = []
        for provider, status in main_engine._last_status.items():
            satellites.append({
                "provider": status.get("provider", provider),
                "mode": status.get("mode"),
                "checked_at": status.get("checked_at"),
                "error": status.get("error"),
            })
        return {
            "satellites": satellites,
            "satellite_count": len(satellites),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_geoshield_health(self) -> dict[str, Any]:
        base = main_engine.get_system_status()
        live_count = sum(1 for s in main_engine._last_status.values() if s.get("mode") == "live")
        mock_count = sum(1 for s in main_engine._last_status.values() if s.get("mode") == "mock")
        return {
            **base,
            "live_connectors": live_count,
            "mock_connectors": mock_count,
            "registered_engine_count": len(main_engine.registered_engines),
        }

    def get_history(self, engine: str | None = None, county: str | None = None, hours: int = 24) -> dict[str, Any]:
        if not DB_PATH.exists():
            return {"points": []}

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = "SELECT engine, county, metric, value, mode, recorded_at FROM analytics_history WHERE recorded_at >= ?"
        params: list[Any] = [cutoff]

        if engine:
            query += " AND engine = ?"
            params.append(engine)
        if county:
            query += " AND county = ?"
            params.append(county)

        query += " ORDER BY recorded_at ASC"
        cur.execute(query, params)
        points = [dict(row) for row in cur.fetchall()]
        conn.close()

        return {"points": points, "count": len(points)}


    def run_snapshot_cycle(self) -> None:
        """One full pass: pulls all counties from each registered engine's
        analyse(), and writes one severity_rank row per county per engine
        into analytics_history. Called on a timer, not per-request."""
        from backend.disaster.agriculture_engine import agriculture_engine
        from backend.disaster.fire_engine import fire_engine
        from backend.disaster.earthquake_engine import earthquake_engine
        from backend.disaster.drought_engine import drought_engine
        from backend.disaster.flood_engine import flood_engine

        now_note = datetime.now(timezone.utc).isoformat()

        try:
            for record in agriculture_engine.analyse():
                county = record.get("county")
                if not county:
                    continue
                severity = record.get("severity")
                mode = record.get("weather_mode", "live")
                if severity in SEVERITY_RANK:
                    main_engine.submit_engine_output(
                        engine="agriculture", county=county,
                        metric="severity_rank", value=float(SEVERITY_RANK[severity]),
                        mode=mode,
                    )
                if record.get("ndvi") is not None:
                    main_engine.submit_engine_output(
                        engine="agriculture", county=county,
                        metric="ndvi", value=float(record["ndvi"]), mode=mode,
                    )
                if record.get("rainfall_mm") is not None:
                    main_engine.submit_engine_output(
                        engine="agriculture", county=county,
                        metric="rainfall_mm", value=float(record["rainfall_mm"]), mode=mode,
                    )
                if record.get("temperature_c") is not None:
                    main_engine.submit_engine_output(
                        engine="agriculture", county=county,
                        metric="temperature_c", value=float(record["temperature_c"]), mode=mode,
                    )
        except Exception as exc:
            print(f"[AnalyticsEngine] snapshot: agriculture failed: {exc!r}")

        try:
            best: dict[str, str] = {}
            for record in fire_engine.analyse():
                county = record.get("county")
                severity = record.get("severity")
                if not county or severity not in SEVERITY_RANK:
                    continue
                if county not in best or SEVERITY_RANK[severity] > SEVERITY_RANK[best[county]]:
                    best[county] = severity
            for county, severity in best.items():
                main_engine.submit_engine_output(
                    engine="fire", county=county,
                    metric="severity_rank", value=float(SEVERITY_RANK[severity]), mode="live",
                )
        except Exception as exc:
            print(f"[AnalyticsEngine] snapshot: fire failed: {exc!r}")

        try:
            best_eq: dict[str, str] = {}
            for record in earthquake_engine.analyse():
                county = record.get("county")
                severity = record.get("severity")
                if not county or severity not in SEVERITY_RANK:
                    continue
                if county not in best_eq or SEVERITY_RANK[severity] > SEVERITY_RANK[best_eq[county]]:
                    best_eq[county] = severity
            for county, severity in best_eq.items():
                main_engine.submit_engine_output(
                    engine="earthquake", county=county,
                    metric="severity_rank", value=float(SEVERITY_RANK[severity]), mode="live",
                )
        except Exception as exc:
            print(f"[AnalyticsEngine] snapshot: earthquake failed: {exc!r}")

        try:
            for record in drought_engine.analyse():
                county = record.get("county")
                severity = record.get("severity")
                mode = record.get("weather_mode", "live")
                if county and severity in SEVERITY_RANK:
                    main_engine.submit_engine_output(
                        engine="drought", county=county,
                        metric="severity_rank", value=float(SEVERITY_RANK[severity]),
                        mode=mode,
                    )
        except Exception as exc:
            print(f"[AnalyticsEngine] snapshot: drought failed: {exc!r}")

        try:
            for record in flood_engine.analyse():
                county = record.get("county")
                severity = record.get("severity")
                mode = record.get("weather_mode", "live")
                if county and severity in SEVERITY_RANK:
                    main_engine.submit_engine_output(
                        engine="flood", county=county,
                        metric="severity_rank", value=float(SEVERITY_RANK[severity]),
                        mode=mode,
                    )
        except Exception as exc:
            print(f"[AnalyticsEngine] snapshot: flood failed: {exc!r}")

        print(f"[AnalyticsEngine] snapshot cycle complete at {now_note}")

analytics_engine = AnalyticsEngine()
