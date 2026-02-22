"""
API Client for aircloudhome.

This module provides the API client for communicating with the AirCloud Home API.
It handles authentication, device data fetching, and device control operations.

For more information on creating API clients:
https://developers.home-assistant.io/docs/api_lib_index
"""

from __future__ import annotations

import asyncio
import socket
from typing import Any

import aiohttp


class AirCloudHomeApiClientError(Exception):
    """Base exception to indicate a general API error."""


class AirCloudHomeApiClientCommunicationError(
    AirCloudHomeApiClientError,
):
    """Exception to indicate a communication error with the API."""


class AirCloudHomeApiClientAuthenticationError(
    AirCloudHomeApiClientError,
):
    """Exception to indicate an authentication error with the API."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """
    Verify that the API response is valid.

    Raises appropriate exceptions for authentication and HTTP errors.

    Args:
        response: The aiohttp ClientResponse to verify.

    Raises:
        AirCloudHomeApiClientAuthenticationError: For 401/403 errors.
        aiohttp.ClientResponseError: For other HTTP errors.

    """
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise AirCloudHomeApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class AirCloudHomeApiClient:
    """
    API Client for AirCloud Home AC integration.

    This client handles communication with the AirCloud Home API for controlling
    Shirokuma AC units. It manages authentication, device discovery, and device control.

    For more information on API clients:
    https://developers.home-assistant.io/docs/api_lib_index

    Attributes:
        _email: The email for API authentication.
        _password: The password for API authentication.
        _session: The aiohttp ClientSession for making requests.
        _access_token: The current access token for API requests.
        _refresh_token: The refresh token for obtaining new access tokens.

    """

    _BASE_URL = "https://api-kuma.aircloudhome.com"

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """
        Initialize the API Client with credentials.

        Args:
            email: The email for authentication from config flow.
            password: The password for authentication from config flow.
            session: The aiohttp ClientSession to use for requests.

        """
        self._email = email
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    async def async_sign_in(self) -> dict[str, Any]:
        """
        Sign in to the API and get access/refresh tokens.

        Returns:
            A dictionary with tokens: {"token": access_token, "refreshToken": refresh_token}

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        data = {
            "email": self._email,
            "password": self._password,
        }
        response = await self._api_wrapper(
            method="post",
            url=f"{self._BASE_URL}/iam/auth/sign-in",
            data=data,
        )
        self._access_token = response.get("token")
        self._refresh_token = response.get("refreshToken")
        return response

    async def async_get_family_groups(self) -> list[dict[str, Any]]:
        """
        Get list of family groups for the authenticated user.

        Returns:
            A list of family groups with their details.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        if not self._access_token:
            await self.async_sign_in()

        response = await self._api_wrapper(
            method="get",
            url=f"{self._BASE_URL}/iam/family-account/v2/groups",
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        return response.get("result", [])

    async def async_get_idu_list(self, family_id: int) -> list[dict[str, Any]]:
        """
        Get list of indoor units (IDU) for a family group.

        Args:
            family_id: The family group ID.

        Returns:
            A list of indoor units with their current state.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        if not self._access_token:
            await self.async_sign_in()

        response = await self._api_wrapper(
            method="get",
            url=f"{self._BASE_URL}/rac/ownership/groups/{family_id}/idu-list",
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        return response if isinstance(response, list) else []

    async def async_control_device(
        self,
        rac_id: int,
        family_id: int,
        power: str | None = None,
        mode: str | None = None,
        fan_speed: str | None = None,
        fan_swing: str | None = None,
        idu_temperature: float | None = None,
        humidity: int | None = None,
    ) -> dict[str, Any]:
        """
        Control an AC device.

        All state parameters are required in the API, so this method will fetch
        the current state if not provided for any parameter.

        Args:
            rac_id: The device ID (id from idu-list).
            family_id: The family group ID.
            power: "ON" or "OFF".
            mode: "HEATING", "COOLING", "FAN", "DRY", "DRY_COOL", "AUTO", or "UNKNOWN".
            fan_speed: "AUTO", "LV1", "LV2", "LV3", "LV4", or "LV5".
            fan_swing: "AUTO", "OFF", "VERTICAL", "HORIZONTAL", or "ALL".
            idu_temperature: Target temperature (0.5 degree increments, 16-32 range).
            humidity: Target humidity (5% increments, 40-60 range).

        Returns:
            The API response with command ID.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        if not self._access_token:
            await self.async_sign_in()

        # All parameters are required for the API
        data = {
            "power": power or "ON",
            "mode": mode or "AUTO",
            "fanSpeed": fan_speed or "AUTO",
            "fanSwing": fan_swing or "AUTO",
            "iduTemperature": idu_temperature if idu_temperature is not None else 22.0,
        }
        if humidity is not None:
            data["humidity"] = humidity

        return await self._api_wrapper(
            method="put",
            url=f"{self._BASE_URL}/rac/basic-idu-control/general-control-command/{rac_id}?familyId={family_id}",
            data=data,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """
        Wrapper for API requests with error handling.

        This method handles all HTTP requests and translates exceptions
        into integration-specific exceptions.

        Args:
            method: The HTTP method (get, post, patch, etc.).
            url: The URL to request.
            data: Optional data to send in the request body.
            headers: Optional headers to include in the request.

        Returns:
            The JSON response from the API.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        try:
            async with asyncio.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise AirCloudHomeApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise AirCloudHomeApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:
            msg = f"Something really wrong happened! - {exception}"
            raise AirCloudHomeApiClientError(
                msg,
            ) from exception
