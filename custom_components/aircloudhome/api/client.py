"""
API Client for aircloudhome.

This module provides the API client for communicating with the AirCloud Home API.
It handles authentication, device data fetching, and device control operations.

For more information on creating API clients:
https://developers.home-assistant.io/docs/api_lib_index
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from enum import StrEnum
import logging
import re
import socket
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Refresh tokens this many seconds before their stated expiry to account for
# clock skew and network latency.
_EXPIRY_BUFFER = timedelta(seconds=60)

# Headers sent by the official mobile apps. The Europe / global API answers
# idu-list with 403 "Access Denied" without them; the Japan API accepts them.
_DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=UTF-8",
    "User-Agent": "okhttp/4.2.2",
}

# Supported target humidity range. Other values mean the unit has no humidity
# control (the Europe / global API reports 2147483647), so the key is dropped.
_HUMIDITY_RANGE = range(40, 61)

# Masked serial numbers such as "XXXX-XXXX-XXXX" (Europe / global API).
_PLACEHOLDER_SERIAL_PATTERN = re.compile(r"^[Xx]+(?:[-\s][Xx]+)*$")


class AirCloudHomeRegion(StrEnum):
    """
    AirCloud Home cloud region.

    Accounts are bound to the region of the mobile app they were created with
    and cannot sign in to the other region's API.
    """

    JAPAN = "japan"
    """Shirokuma-kun app (白くまくんアプリ), Japan."""

    GLOBAL = "global"
    """airCloud Go / AirCloud Home app, Europe and the rest of the world."""


API_BASE_URLS: dict[AirCloudHomeRegion, str] = {
    AirCloudHomeRegion.JAPAN: "https://api-kuma.aircloudhome.com",
    AirCloudHomeRegion.GLOBAL: "https://api-global-prod.aircloudhome.com",
}


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
        _base_url: The API base URL of the account's region.
        _email: The email for API authentication.
        _password: The password for API authentication.
        _session: The aiohttp ClientSession for making requests.
        _access_token: The current access token for API requests.
        _refresh_token: The refresh token for obtaining new access tokens.
        _access_token_expires_at: UTC datetime when the access token expires
            (``None`` if expiry is unknown).
        _refresh_token_expires_at: UTC datetime when the refresh token expires
            (``None`` if expiry is unknown).

    """

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
        region: AirCloudHomeRegion | str = AirCloudHomeRegion.JAPAN,
    ) -> None:
        """
        Initialize the API Client with credentials.

        Args:
            email: The email for authentication from config flow.
            password: The password for authentication from config flow.
            session: The aiohttp ClientSession to use for requests.
            region: The cloud region the account belongs to. Defaults to Japan,
                the only region supported by earlier versions.

        Raises:
            ValueError: If ``region`` is not a known region.

        """
        self._base_url = API_BASE_URLS[AirCloudHomeRegion(region)]
        self._email = email
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._access_token_expires_at: datetime | None = None
        self._refresh_token_expires_at: datetime | None = None
        self._refresh_lock = asyncio.Lock()

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
            url=f"{self._base_url}/iam/auth/sign-in",
            data=data,
        )
        self._store_tokens(response)
        return response

    async def async_refresh_token(self) -> dict[str, Any]:
        """
        Refresh the access token using the refresh token.

        Uses the current refresh token to obtain a new access token without
        requiring the user to supply credentials again.

        Returns:
            A dictionary with the new tokens.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If the refresh token is
                invalid or expired. The caller should trigger re-authentication.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        if not self._refresh_token:
            msg = "No refresh token available - re-authentication required"
            raise AirCloudHomeApiClientAuthenticationError(msg)

        response = await self._api_wrapper(
            method="post",
            url=f"{self._base_url}/iam/auth/refresh-token",
            headers={
                "Authorization": f"Bearer {self._refresh_token}",
                "isRefreshToken": "true",
            },
            _is_retry=True,
        )
        self._store_tokens(response)
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
        await self._async_ensure_valid_token()

        response = await self._api_wrapper(
            method="get",
            url=f"{self._base_url}/iam/family-account/v2/groups",
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        return response.get("result", [])

    async def async_get_idu_list(self, family_id: int) -> list[dict[str, Any]]:
        """
        Get list of indoor units (IDU) for a family group.

        Args:
            family_id: The family group ID.

        Returns:
            A list of indoor units with their current state, normalized by
            ``normalize_device_list``.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        await self._async_ensure_valid_token()

        response = await self._api_wrapper(
            method="get",
            url=f"{self._base_url}/rac/ownership/groups/{family_id}/idu-list",
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        return normalize_device_list(response)

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
            fan_swing: "AUTO", "OFF", "VERTICAL", "HORIZONTAL", or "BOTH".
            idu_temperature: Target temperature (0.5 degree increments, 16-32 range).
            humidity: Target humidity (5% increments, 40-60 range).

        Returns:
            The API response with command ID.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        await self._async_ensure_valid_token()

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
            url=f"{self._base_url}/rac/basic-idu-control/general-control-command/{rac_id}?familyId={family_id}",
            data=data,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
        _is_retry: bool = False,
    ) -> Any:
        """
        Wrapper for API requests with error handling and transparent token refresh.

        On a 401 response, this method automatically attempts to refresh the
        access token (once) and retries the original request. If the refresh
        also fails with a 401, an ``AirCloudHomeApiClientAuthenticationError``
        is raised so the coordinator can trigger a re-authentication flow.

        Args:
            method: The HTTP method (get, post, patch, etc.).
            url: The URL to request.
            data: Optional data to send in the request body.
            headers: Optional headers to include in the request.
            _is_retry: Internal flag – set to ``True`` when this call is
                already a retry after token refresh, preventing infinite loops.

        Returns:
            The JSON response from the API.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If authentication fails
                and cannot be resolved by refreshing the token.
            AirCloudHomeApiClientCommunicationError: If communication fails.
            AirCloudHomeApiClientError: For other API errors.

        """
        try:
            async with asyncio.timeout(10):
                _LOGGER.debug("API %s %s body=%s", method.upper(), url, data)
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers={**_DEFAULT_HEADERS, **(headers or {})},
                    json=data,
                )
                needs_refresh = response.status == 401 and not _is_retry
                if not needs_refresh:
                    if response.status >= 400:
                        error_body = await response.text()
                        _LOGGER.error("API error %s from %s: %s", response.status, url, error_body)
                    _verify_response_or_raise(response)
                    return await response.json()

            # Perform token refresh outside the request timeout so that the
            # refresh request gets its own independent 10-second window.
            await self._async_ensure_valid_token()
            # Rebuild Authorization header with the new access token.
            refreshed_headers = dict(headers or {})
            refreshed_headers["Authorization"] = f"Bearer {self._access_token}"
            return await self._api_wrapper(
                method=method,
                url=url,
                data=data,
                headers=refreshed_headers,
                _is_retry=True,
            )

        except AirCloudHomeApiClientError:
            raise
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

    def _store_tokens(self, response: dict[str, Any]) -> None:
        """
        Persist tokens and their expiry datetimes from an API response.

        Parses ``access_token_expires_in`` and ``refresh_token_expires_in``
        (both in **milliseconds** as returned by the API) and converts them to
        absolute UTC datetimes so that expiry can be checked without an extra
        API round-trip.

        If an ``expires_in`` field is absent the corresponding expiry datetime
        is set to ``None``, which is treated as "unknown / assume still valid".
        The refresh-token expiry is only *updated* when the response contains a
        new ``refreshToken``; otherwise the previously stored expiry is kept.

        Args:
            response: The decoded JSON response from ``sign-in`` or
                ``refresh-token``.

        """
        now = datetime.now(UTC)
        if token := response.get("token"):
            self._access_token = token
            if (expires_ms := response.get("access_token_expires_in")) is not None:
                self._access_token_expires_at = now + timedelta(milliseconds=expires_ms)
            else:
                self._access_token_expires_at = None

        if new_refresh := response.get("refreshToken"):
            self._refresh_token = new_refresh
            if (expires_ms := response.get("refresh_token_expires_in")) is not None:
                self._refresh_token_expires_at = now + timedelta(milliseconds=expires_ms)
            # If the response does not include a new refresh token expiry, keep
            # the previously stored value unchanged.

    def _is_access_token_valid(self) -> bool:
        """
        Return ``True`` when the access token exists and has not yet expired.

        A safety buffer (``_EXPIRY_BUFFER``) is subtracted from the stored
        expiry so that the token is not used right at the boundary. When no
        expiry information is available the token is assumed to be valid.

        """
        if not self._access_token:
            return False
        if self._access_token_expires_at is None:
            return True
        return datetime.now(UTC) < self._access_token_expires_at - _EXPIRY_BUFFER

    def _is_refresh_token_valid(self) -> bool:
        """
        Return ``True`` when the refresh token exists and has not yet expired.

        A safety buffer (``_EXPIRY_BUFFER``) is subtracted from the stored
        expiry so that the token is not used right at the boundary. When no
        expiry information is available the token is assumed to be valid.

        """
        if not self._refresh_token:
            return False
        if self._refresh_token_expires_at is None:
            return True
        return datetime.now(UTC) < self._refresh_token_expires_at - _EXPIRY_BUFFER

    async def _async_ensure_valid_token(self) -> None:
        """
        Ensure the access token is valid before making an API request.

        Called both proactively (at the start of every public API method) and
        reactively (after a 401 response inside ``_api_wrapper``). In the
        reactive case the pre-lock fast path rarely fires, but it is still
        correct: if another coroutine refreshed the token while the current
        request was in flight, there is no need to refresh again.

        Decision tree (protected by ``_refresh_lock`` to serialise concurrent
        callers):

        1. Access token is still valid → do nothing.
        2. Access token expired / missing, refresh token valid → refresh.
        3. Both tokens expired / missing → full sign-in with credentials.

        Raises:
            AirCloudHomeApiClientAuthenticationError: If sign-in fails.
            AirCloudHomeApiClientCommunicationError: If communication fails.

        """
        if self._is_access_token_valid():
            return

        async with self._refresh_lock:
            # Re-check inside the lock: another coroutine may have already
            # refreshed the token while this one was waiting.
            if self._is_access_token_valid():
                return

            if self._is_refresh_token_valid():
                await self.async_refresh_token()
            else:
                await self.async_sign_in()


def normalize_device_list(response: Any) -> list[dict[str, Any]]:
    """
    Normalize an ``idu-list`` response into a list of device payloads.

    The Europe / global API fills fields the Japan API leaves out with
    placeholders. They are removed here so entities can rely on one format:

    - ``humidity`` is kept only when it is a valid target (40-60 %); otherwise
      the unit is treated as having no humidity control.
    - Masked serial numbers (``XXXX-XXXX-XXXX``) are removed.

    Args:
        response: The decoded JSON response (a list of device objects).

    Returns:
        A list of normalized device dictionaries (copies of the input).

    """
    if not isinstance(response, list):
        return []
    return [_normalize_device(item) for item in response if isinstance(item, dict)]


def _normalize_device(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single device payload. See ``normalize_device_list``."""
    device = dict(item)

    humidity = device.pop("humidity", None)
    if isinstance(humidity, (int, float)) and not isinstance(humidity, bool) and int(humidity) in _HUMIDITY_RANGE:
        device["humidity"] = int(humidity)

    serial_number = device.pop("serialNumber", None)
    if (
        isinstance(serial_number, str)
        and (serial_number := serial_number.strip())
        and not _PLACEHOLDER_SERIAL_PATTERN.fullmatch(serial_number)
    ):
        device["serialNumber"] = serial_number

    return device
