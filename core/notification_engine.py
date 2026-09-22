from __future__ import annotations

from typing import Any

from core.config import settings


class NotificationEngine:
    """
    Provider-independent GeoShield notification service.

    SMS delivery is dry-run by default.
    Actual provider requests require:
      - GEOSHIELD_NOTIFICATIONS_ENABLED=true
      - Africa's Talking credentials
      - dry_run=False on the send call
    """

    def __init__(self):
        self.settings = settings

    @staticmethod
    def format_sms(alert: dict[str, Any]) -> str:
        hazard = str(alert.get("hazard", "hazard")).upper()
        severity = str(alert.get("severity", "Unknown"))
        location = str(alert.get("county") or "Location unavailable")
        message = str(
            alert.get("message") or f"{severity} {hazard} risk detected."
        )
        action = str(
            alert.get("recommended_action") or "MONITOR"
        )

        sms = (
            f"GEOSHIELD {severity.upper()} ALERT | {hazard}. "
            f"{message} Area: {location}. Action: {action}."
        )

        # Keep the alert concise for SMS delivery.
        return sms[:480]

    def send_sms(
        self,
        alert: dict[str, Any],
        *,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        Send an alert by SMS.

        dry_run=True never contacts Africa's Talking.
        A real request requires notifications to be explicitly enabled.
        """

        if not isinstance(alert, dict):
            return {
                "status": "failed",
                "provider": "africastalking",
                "reason": "Alert must be a dictionary.",
            }

        recipient = self.settings.geoshield_alert_sms_recipient.strip()
        message = self.format_sms(alert)

        if not recipient:
            return {
                "status": "unavailable",
                "provider": "africastalking",
                "reason": "SMS recipient is not configured.",
            }

        if dry_run:
            return {
                "status": "dry_run",
                "provider": "africastalking",
                "recipient_configured": True,
                "message": message,
                "sent": False,
            }

        if not self.settings.notifications_enabled:
            return {
                "status": "disabled",
                "provider": "africastalking",
                "reason": (
                    "Notifications are disabled. "
                    "Set GEOSHIELD_NOTIFICATIONS_ENABLED=true "
                    "to permit provider requests."
                ),
                "sent": False,
            }

        username = self.settings.africastalking_username.strip()
        api_key = self.settings.africastalking_api_key.strip()

        if not username or not api_key:
            return {
                "status": "unavailable",
                "provider": "africastalking",
                "reason": "Africa's Talking credentials are missing.",
                "sent": False,
            }

        try:
            import africastalking

            africastalking.initialize(username, api_key)
            sms_service = africastalking.SMS

            sender_id = self.settings.africastalking_sender_id.strip()

            if sender_id:
                response = sms_service.send(
                    message,
                    [recipient],
                    sender_id=sender_id,
                )
            else:
                response = sms_service.send(
                    message,
                    [recipient],
                )

            return {
                "status": "submitted",
                "provider": "africastalking",
                "response": response,
                "sent": True,
            }

        except Exception as exc:
            # Do not expose credentials or interrupt the alert pipeline.
            return {
                "status": "failed",
                "provider": "africastalking",
                "reason": str(exc),
                "sent": False,
            }
