"""
Credential validators.

Validation functions for user credentials and authentication.

When this file grows, consider splitting into:
- credentials.py: Basic credential validation
- oauth.py: OAuth-specific validation
- api_auth.py: API authentication methods
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.aircloudhome.api import AirCloudHomeApiClient, AirCloudHomeRegion
from homeassistant.helpers.aiohttp_client import async_create_clientsession

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def validate_credentials(
    hass: HomeAssistant,
    email: str,
    password: str,
    region: AirCloudHomeRegion | str = AirCloudHomeRegion.JAPAN,
) -> None:
    """
    Validate user credentials by testing API connection.

    Args:
        hass: Home Assistant instance.
        email: The email to validate.
        password: The password to validate.
        region: The cloud region the account belongs to.

    Raises:
        AirCloudHomeApiClientAuthenticationError: If credentials are invalid.
        AirCloudHomeApiClientCommunicationError: If communication fails.
        AirCloudHomeApiClientError: For other API errors.

    """
    client = AirCloudHomeApiClient(
        email=email,
        password=password,
        session=async_create_clientsession(hass),
        region=region,
    )
    await client.async_sign_in()  # May raise authentication/communication errors


__all__ = [
    "validate_credentials",
]
