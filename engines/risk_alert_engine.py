"""
GeoShield AI Enterprise
Central Risk Alert Engine

Coordinates hazard-specific risk evaluation and converts risk results
into standardized GeoShield alerts.

Actual risk calculations remain in core.risk_engine.RiskEngine.
This module is responsible for:
    - registering hazard handlers
    - evaluating hazards
    - standardizing alerts
    - publishing alerts to EventBus
    - maintaining alert history
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


class RiskAlertEngine:
    """
    Central registry and coordinator for GeoShield risk alerts.

    Hazard-specific risk calculations are delegated to registered
    handlers. The RiskAlertEngine does not duplicate risk formulas.
    """

    def __init__(self, event_bus=None):
        self.handlers: dict[str, Callable[[dict], dict]] = {}
        self.alert_history: list[dict] = []
        self.event_bus = event_bus

    # ---------------------------------------------------------
    # HAZARD REGISTRATION
    # ---------------------------------------------------------

    def register(
        self,
        hazard: str,
        risk_handler: Callable[[dict], dict],
    ) -> None:
        """
        Register a hazard and its risk-calculation handler.
        """

        hazard_name = hazard.strip().lower()

        if not hazard_name:
            raise ValueError("Hazard name cannot be empty.")

        if not callable(risk_handler):
            raise TypeError(
                f"Risk handler for '{hazard_name}' must be callable."
            )

        self.handlers[hazard_name] = risk_handler

    def unregister(self, hazard: str) -> None:
        """Remove a registered hazard."""

        self.handlers.pop(
            hazard.strip().lower(),
            None,
        )

    def exists(self, hazard: str) -> bool:
        """Return whether a hazard is registered."""

        return hazard.strip().lower() in self.handlers

    def list_hazards(self) -> list[str]:
        """Return all registered hazards."""

        return list(self.handlers.keys())

    # ---------------------------------------------------------
    # RISK EVALUATION
    # ---------------------------------------------------------

    def evaluate(
        self,
        hazard: str,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evaluate a hazard and produce a standardized GeoShield alert.
        """

        hazard_name = hazard.strip().lower()

        if hazard_name not in self.handlers:
            raise ValueError(
                f"No risk handler registered for hazard: {hazard_name}"
            )

        if not isinstance(event, dict):
            raise TypeError("Event must be a dictionary.")

        risk_result = self.handlers[hazard_name](event)

        if not isinstance(risk_result, dict):
            raise TypeError(
                f"Risk handler for '{hazard_name}' must return a dictionary."
            )

        risk_score = float(
            risk_result.get("risk_score", 0)
        )

        severity = risk_result.get(
            "severity",
            self.classify_severity(risk_score),
        )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        alert = {
            "alert_id": self._generate_alert_id(
                hazard_name
            ),
            "hazard": hazard_name,
            "risk_score": risk_score,
            "severity": severity,
            "latitude": event.get("latitude"),
            "longitude": event.get("longitude"),
            "county": event.get("county"),
            "message": self.build_message(
                hazard_name,
                severity,
            ),
            "recommended_action": self.build_action(
                severity,
            ),
            "source": event.get(
                "source",
                "GeoShield Intelligence Engine",
            ),
            "timestamp": timestamp,
        }

        # Preserve original risk information.
        alert["risk"] = risk_result

        # Preserve useful event information.
        alert["event"] = event

        self.alert_history.append(alert)

        if self.event_bus is not None:
            self.event_bus.publish(alert)

        return alert

    # ---------------------------------------------------------
    # SEVERITY
    # ---------------------------------------------------------

    @staticmethod
    def classify_severity(
        risk_score: float,
    ) -> str:

        if risk_score >= 90:
            return "Extreme"

        if risk_score >= 70:
            return "High"

        if risk_score >= 50:
            return "Moderate"

        return "Low"

    # ---------------------------------------------------------
    # ALERT MESSAGE
    # ---------------------------------------------------------

    @staticmethod
    def build_message(
        hazard: str,
        severity: str,
    ) -> str:

        messages = {
            "fire": {
                "Extreme": "Extreme wildfire risk detected.",
                "High": "High wildfire risk detected.",
                "Moderate": "Moderate wildfire risk detected.",
                "Low": "Low wildfire risk detected.",
            },

            "flood": {
                "Extreme": "Extreme flood risk detected.",
                "High": "High flood risk detected.",
                "Moderate": "Moderate flood risk detected.",
                "Low": "Low flood risk detected.",
            },

            "earthquake": {
                "Extreme": "Extreme earthquake impact risk detected.",
                "High": "High earthquake impact risk detected.",
                "Moderate": "Moderate earthquake impact risk detected.",
                "Low": "Low earthquake impact risk detected.",
            },

            "agriculture": {
                "Extreme": "Extreme agricultural stress detected.",
                "High": "High agricultural stress detected.",
                "Moderate": "Moderate agricultural stress detected.",
                "Low": "Low agricultural stress detected.",
            },

            "vegetation": {
                "Extreme": "Extreme vegetation stress detected.",
                "High": "High vegetation stress detected.",
                "Moderate": "Moderate vegetation stress detected.",
                "Low": "Low vegetation stress detected.",
            },

            "drought": {
                "Extreme": "Extreme drought risk detected.",
                "High": "High drought risk detected.",
                "Moderate": "Moderate drought risk detected.",
                "Low": "Low drought risk detected.",
            },

            "flood": {
                "Extreme": "Extreme flood risk detected.",
                "High": "High flood risk detected.",
                "Moderate": "Moderate flood risk detected.",
                "Low": "Low flood risk detected.",
            },
        }

        return messages.get(
            hazard,
            {},
        ).get(
            severity,
            f"{severity} {hazard} risk detected.",
        )

    # ---------------------------------------------------------
    # RECOMMENDED ACTION
    # ---------------------------------------------------------

    @staticmethod
    def build_action(
        severity: str,
    ) -> str:

        actions = {
            "Extreme": "IMMEDIATE_RESPONSE",
            "High": "PRIORITY_FIELD_ASSESSMENT",
            "Moderate": "ENHANCED_MONITORING",
            "Low": "ROUTINE_MONITORING",
        }

        return actions.get(
            severity,
            "MONITOR",
        )

    # ---------------------------------------------------------
    # ALERT ID
    # ---------------------------------------------------------

    def _generate_alert_id(
        self,
        hazard: str,
    ) -> str:

        return (
            f"GS-{hazard.upper()}-"
            f"{len(self.alert_history) + 1:06d}"
        )

    # ---------------------------------------------------------
    # HISTORY
    # ---------------------------------------------------------

    def history(self) -> list[dict]:
        """Return all alerts generated during this runtime."""

        return list(self.alert_history)

    def latest(
        self,
        limit: int = 10,
    ) -> list[dict]:

        if limit < 1:
            return []

        return self.alert_history[-limit:]


# ---------------------------------------------------------
# DEFAULT REGISTRATION
# ---------------------------------------------------------

def build_risk_alert_engine(
    risk_engine,
    event_bus=None,
) -> RiskAlertEngine:
    """
    Build the GeoShield Risk Alert Engine and register
    all currently supported risk calculations.
    """

    engine = RiskAlertEngine(
        event_bus=event_bus
    )

    # FIRE
    engine.register(
        "fire",
        risk_engine.calculate_fire_risk,
    )

    # EARTHQUAKE
    engine.register(
        "earthquake",
        risk_engine.calculate_earthquake_risk,
    )

    # AGRICULTURE
    engine.register(
        "agriculture",
        risk_engine.calculate_agriculture_risk,
    )

    # DROUGHT
    engine.register(
        "drought",
        risk_engine.calculate_drought_risk,
    )

    # FLOOD
    engine.register(
        "flood",
        risk_engine.calculate_flood_risk,
    )

    return engine


__all__ = [
    "RiskAlertEngine",
    "build_risk_alert_engine",
]
