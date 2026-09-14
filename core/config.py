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
    # Runtime
    # ---------------------------------------------------------

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


