"""
GeoShield AI Enterprise
Central Environment Configuration

Secure centralized configuration for:
- GeoShield runtime
- Copernicus Data Space Ecosystem
- Planet
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT LOADING
# ============================================================

# Load the project .env file.
#
# Values already present in the operating-system environment
# take precedence because override=False.
load_dotenv(".env", override=False)


# ============================================================
# GEOSHIELD SETTINGS
# ============================================================

@dataclass(frozen=True)
class GeoShieldSettings:
    """Centralized GeoShield runtime configuration."""

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------

    app_name: str = "GeoShield AI Enterprise"

    environment: str = os.getenv(
        "GEOSHIELD_ENV",
        "development",
    )

    # ---------------------------------------------------------
    # Copernicus Data Space Ecosystem
    # ---------------------------------------------------------

    cdse_username: str = os.getenv(
        "CDSE_USERNAME",
        "",
    )

    cdse_password: str = os.getenv(
        "CDSE_PASSWORD",
        "",
    )

    cdse_client_id: str = os.getenv(
        "CDSE_CLIENT_ID",
        "cdse-public",
    )

    cdse_token_url: str = os.getenv(
        "CDSE_TOKEN_URL",
        (
            "https://identity.dataspace.copernicus.eu/"
            "auth/realms/CDSE/protocol/openid-connect/token"
        ),
    )

    cdse_catalog_url: str = os.getenv(
        "CDSE_CATALOG_URL",
        (
            "https://catalogue.dataspace.copernicus.eu/"
            "odata/v1/Products"
        ),
    )

    # ---------------------------------------------------------
    # NASA FIRMS (VIIRS active fire / thermal data)
    # ---------------------------------------------------------

    firms_map_key: str = os.getenv(
        "FIRMS_MAP_KEY",
        "",
    )

    # ---------------------------------------------------------
    # NASA GPM / IMERG (precipitation, via PPS)
    # ---------------------------------------------------------

    gpm_pps_email: str = os.getenv(
        "GPM_PPS_EMAIL",
        "",
    )

    # ---------------------------------------------------------
    # WorldPop (population exposure)
    # ---------------------------------------------------------

    worldpop_api_key: str = os.getenv(
        "WORLDPOP_API_KEY",
        "",
    )

    # ---------------------------------------------------------
    # Planet
    # ---------------------------------------------------------

    planet_api_key: str = os.getenv(
        "PLANET_API_KEY",
        "",
    )

    planet_client_id: str = os.getenv(
        "PLANET_CLIENT_ID",
        "",
    )

    planet_client_secret: str = os.getenv(
        "PLANET_CLIENT_SECRET",
        "",
    )

    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # Notifications ? Africa's Talking SMS
    # ---------------------------------------------------------

    africastalking_username: str = os.getenv(
        "AFRICASTALKING_USERNAME", ""
    )

    africastalking_api_key: str = os.getenv(
        "AFRICASTALKING_API_KEY", ""
    )

    africastalking_sender_id: str = os.getenv(
        "AFRICASTALKING_SENDER_ID", ""
    )

    africastalking_environment: str = os.getenv(
        "AFRICASTALKING_ENVIRONMENT", "sandbox"
    ).strip().lower()

    # ---------------------------------------------------------
    # GeoShield Alert Recipients
    # ---------------------------------------------------------

    geoshield_alert_sms_recipient: str = os.getenv(
        "GEOSHIELD_ALERT_SMS_RECIPIENT", ""
    )

    geoshield_alert_email_primary: str = os.getenv(
        "GEOSHIELD_ALERT_EMAIL_PRIMARY", ""
    )

    geoshield_alert_email_secondary: str = os.getenv(
        "GEOSHIELD_ALERT_EMAIL_SECONDARY", ""
    )

    # Notifications remain disabled until explicitly enabled.
    notifications_enabled: bool = os.getenv(
        "GEOSHIELD_NOTIFICATIONS_ENABLED", "false"
    ).strip().lower() in {"1", "true", "yes", "on"}

    # Runtime
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # Local data directory (kept off any cloud-synced folder --
    # SQLite and other local data files should live here, not
    # under the project folder, to avoid cloud-sync I/O latency)
    # ---------------------------------------------------------

    data_dir: str = os.getenv(
        "GEOSHIELD_DATA_DIR",
        os.path.join(os.getenv("LOCALAPPDATA", "C:/GeoShield_data"), "GeoShield"),
    )

    # Reports Engine narrative generation (separate key from Disaster Video Studio).
    reports_gemini_api_key: str = os.getenv("GEOSHIELD_REPORTS_GEMINI_API_KEY", "")

    http_timeout: float = float(
        os.getenv(
            "GEOSHIELD_HTTP_TIMEOUT",
            "60",
        )
    )


# ============================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================

settings = GeoShieldSettings()


