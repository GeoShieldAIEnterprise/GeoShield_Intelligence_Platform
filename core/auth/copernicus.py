"""
GeoShield AI Enterprise
Copernicus Authentication Manager
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass

import requests

from core.config import settings
from core.auth.exceptions import (
    CopernicusAuthenticationError,
    CopernicusConfigurationError,
    CopernicusNetworkError,
)


@dataclass
class TokenState:
    """Runtime state of a Copernicus access token."""

    access_token: str | None = None
    expires_at: float = 0.0


class CopernicusAuthManager:
    """Manage Copernicus authentication and token lifecycle."""

    def __init__(self, max_retries: int = 2) -> None:
        self.state = TokenState()
        self.max_retries = max(0, max_retries)

    def is_token_valid(self) -> bool:
        """Return True when a usable token is currently cached."""

        token = self.state.access_token

        return (
            token is not None
            and bool(token)
            and time.time() < self.state.expires_at
        )

    def seconds_remaining(self) -> float:
        """Return remaining lifetime of the cached token."""

        if not self.is_token_valid():
            return 0.0

        remaining = self.state.expires_at - time.time()

        return max(remaining, 0.0)

    def _validate_configuration(self) -> None:
        """Validate required Copernicus configuration."""

        if not settings.cdse_username:
            raise CopernicusConfigurationError(
                "CDSE username is not configured."
            )

        if not settings.cdse_password:
            raise CopernicusConfigurationError(
                "CDSE password is not configured."
            )

        if not settings.cdse_client_id:
            raise CopernicusConfigurationError(
                "CDSE client ID is not configured."
            )

        if not settings.cdse_token_url:
            raise CopernicusConfigurationError(
                "CDSE token URL is not configured."
            )

    def authenticate(self) -> str:
        """Authenticate against Copernicus Data Space via curl (Schannel), bypassing an OpenSSL/renegotiation incompatibility with this server."""

        self._validate_configuration()

        attempts = self.max_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                result = subprocess.run(
                    [
                        "curl.exe", "-s", "--max-time", "20",
                        "-X", "POST",
                        settings.cdse_token_url,
                        "--data-urlencode", "grant_type=password",
                        "--data-urlencode", f"client_id={settings.cdse_client_id}",
                        "--data-urlencode", f"username={settings.cdse_username}",
                        "--data-urlencode", f"password={settings.cdse_password}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=25,
                )

            except (subprocess.SubprocessError, OSError) as exc:
                if attempt >= attempts:
                    raise CopernicusNetworkError(
                        "Unable to reach Copernicus authentication service."
                    ) from exc

                time.sleep(1)
                continue

            if result.returncode != 0:
                if attempt >= attempts:
                    raise CopernicusNetworkError(
                        f"curl failed with code {result.returncode}: {result.stderr}"
                    )

                time.sleep(1)
                continue

            try:
                payload = json.loads(result.stdout)

            except ValueError as exc:
                raise CopernicusAuthenticationError(
                    "Copernicus returned an invalid authentication response."
                ) from exc

            if "error" in payload:
                detail = f" Error: {payload.get('error')}."
                description = payload.get("error_description")

                if description:
                    detail += f" {description}"

                raise CopernicusAuthenticationError(
                    "Copernicus rejected the authentication request." + detail
                )

            token = payload.get("access_token")

            if not isinstance(token, str) or not token:
                raise CopernicusAuthenticationError(
                    "Copernicus returned no valid access token."
                )

            expires_in = payload.get("expires_in", 1800)

            try:
                expires_in_seconds = int(expires_in)

            except (TypeError, ValueError) as exc:
                raise CopernicusAuthenticationError(
                    "Copernicus returned an invalid token lifetime."
                ) from exc

            safety_margin = 60

            self.state.access_token = token
            self.state.expires_at = (
                time.time()
                + max(expires_in_seconds - safety_margin, 1)
            )

            return token

        raise CopernicusNetworkError(
            "Authentication failed after retry attempts."
        )

    def get_token(self) -> str:
        """Return cached token or authenticate when necessary."""

        if not self.is_token_valid():
            return self.authenticate()

        token = self.state.access_token

        if token is None:
            raise CopernicusAuthenticationError(
                "Token state is invalid: cached token is missing."
            )

        return token
