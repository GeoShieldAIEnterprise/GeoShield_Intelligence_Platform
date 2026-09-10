"""
GeoShield AI Enterprise
Copernicus Authentication Manager
"""

from __future__ import annotations

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
        """Authenticate against Copernicus Data Space."""

        self._validate_configuration()

        attempts = self.max_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(
                    settings.cdse_token_url,
                    data={
                        "grant_type": "password",
                        "client_id": settings.cdse_client_id,
                        "username": settings.cdse_username,
                        "password": settings.cdse_password,
                    },
                    timeout=min(settings.http_timeout, 15),  # auth handshake should never need the full data-download timeout
                )

            except requests.RequestException as exc:
                if attempt >= attempts:
                    raise CopernicusNetworkError(
                        "Unable to reach Copernicus authentication service."
                    ) from exc

                time.sleep(1)
                continue

            if response.status_code in (400, 401, 403):
                detail = ""

                try:
                    payload = response.json()

                    error = payload.get("error")
                    description = payload.get("error_description")

                    if error:
                        detail = f" Error: {error}."

                    if description:
                        detail += f" {description}"

                except ValueError:
                    pass

                raise CopernicusAuthenticationError(
                    "Copernicus rejected the authentication request."
                    + detail
                )

            try:
                response.raise_for_status()

            except requests.RequestException as exc:
                if attempt >= attempts:
                    raise CopernicusNetworkError(
                        "Copernicus authentication request failed."
                    ) from exc

                time.sleep(1)
                continue

            try:
                payload = response.json()

            except ValueError as exc:
                raise CopernicusAuthenticationError(
                    "Copernicus returned an invalid authentication response."
                ) from exc

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