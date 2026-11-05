"""Tests for the AirCloud Home API client."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.aircloudhome.api import API_BASE_URLS, AirCloudHomeApiClient, AirCloudHomeRegion
from custom_components.aircloudhome.api.client import normalize_device_list

pytestmark = pytest.mark.unit


def _session(payload: Any) -> MagicMock:
    """Return a fake aiohttp session whose requests all succeed with ``payload``."""
    response = MagicMock(status=200)
    response.json = AsyncMock(return_value=payload)
    session = MagicMock()
    session.request = AsyncMock(return_value=response)
    return session


def _client(session: MagicMock, region: AirCloudHomeRegion | str = AirCloudHomeRegion.JAPAN) -> AirCloudHomeApiClient:
    return AirCloudHomeApiClient(email="user@example.com", password="secret", session=session, region=region)


@pytest.mark.parametrize(
    ("region", "base_url"),
    [
        (None, "https://api-kuma.aircloudhome.com"),
        (AirCloudHomeRegion.JAPAN, "https://api-kuma.aircloudhome.com"),
        ("global", "https://api-global-prod.aircloudhome.com"),
    ],
)
async def test_sign_in_uses_region_base_url(region: str | None, base_url: str) -> None:
    """Sign-in goes to the base URL of the configured region (Japan by default)."""
    session = _session({"token": "access", "refreshToken": "refresh"})
    if region is None:
        client = AirCloudHomeApiClient(email="user@example.com", password="secret", session=session)
    else:
        client = _client(session, region)

    await client.async_sign_in()

    assert session.request.await_args.kwargs["url"] == f"{base_url}/iam/auth/sign-in"
    assert API_BASE_URLS[AirCloudHomeRegion(region or "japan")] == base_url


def test_unknown_region_is_rejected() -> None:
    """An unknown region fails fast instead of silently using another API."""
    with pytest.raises(ValueError, match="mars"):
        _client(_session({}), "mars")


async def test_requests_include_app_headers() -> None:
    """Every request carries the mobile-app headers plus the per-call headers."""
    session = _session([])
    client = _client(session, AirCloudHomeRegion.GLOBAL)
    client._access_token = "access"  # noqa: SLF001

    assert await client.async_get_idu_list(7) == []

    call = session.request.await_args.kwargs
    assert call["url"] == "https://api-global-prod.aircloudhome.com/rac/ownership/groups/7/idu-list"
    assert call["headers"] == {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "okhttp/4.2.2",
        "Authorization": "Bearer access",
    }


@pytest.mark.parametrize("response", [None, {}, {"result": [{"id": 1}]}, "unexpected"])
def test_normalize_device_list_without_device_list(response: Any) -> None:
    """Anything but a list of devices yields no devices."""
    assert normalize_device_list(response) == []


def test_normalize_device_keeps_valid_payload() -> None:
    """A complete Japan-style payload is kept as is; non-dict entries are dropped."""
    device = {
        "id": 1,
        "power": "ON",
        "humidity": 50,
        "serialNumber": " ABC123 ",
        "online": False,
    }

    (normalized,) = normalize_device_list([device, 42])

    assert normalized == {
        "id": 1,
        "power": "ON",
        "humidity": 50,
        "serialNumber": "ABC123",
        "online": False,
    }
    assert device["serialNumber"] == " ABC123 ", "input must not be mutated"


@pytest.mark.parametrize("humidity", [2147483647, 0, 39, 61, None, True, "50"])
def test_normalize_device_drops_invalid_humidity(humidity: Any) -> None:
    """Out-of-range humidity means the unit has no humidity control."""
    (normalized,) = normalize_device_list([{"id": 1, "humidity": humidity}])
    assert "humidity" not in normalized


@pytest.mark.parametrize("serial_number", ["XXXX-XXXX-XXXX", "XXXXXXXX", "xxxx-xxxx", "XX XX", "  ", "", None, 12345])
def test_normalize_device_drops_placeholder_serial(serial_number: Any) -> None:
    """Masked or missing serial numbers are not exposed in device info."""
    (normalized,) = normalize_device_list([{"id": 1, "serialNumber": serial_number}])
    assert "serialNumber" not in normalized
