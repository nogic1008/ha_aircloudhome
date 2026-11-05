"""Tests for signing in to the AirCloud Home API."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.aircloudhome.api import AirCloudHomeApiClient, AirCloudHomeApiClientAuthenticationError

pytestmark = pytest.mark.unit


def _session(status: int, payload: dict | None = None) -> MagicMock:
    """Return a fake aiohttp session whose requests all answer with ``status``."""
    response = MagicMock(status=status)
    response.json = AsyncMock(return_value=payload or {})
    response.text = AsyncMock(return_value="")
    session = MagicMock()
    session.request = AsyncMock(return_value=response)
    return session


async def test_sign_in_with_invalid_credentials_raises_auth_error() -> None:
    """A 401 on sign-in is reported as an authentication error, not retried via token refresh."""
    session = _session(401)
    client = AirCloudHomeApiClient(email="user@example.com", password="wrong", session=session)

    async with asyncio.timeout(5):
        with pytest.raises(AirCloudHomeApiClientAuthenticationError):
            await client.async_sign_in()

    assert session.request.await_count == 1


async def test_sign_in_stores_tokens() -> None:
    """A successful sign-in sends the credentials once and keeps the returned tokens."""
    session = _session(200, {"token": "access", "refreshToken": "refresh"})
    client = AirCloudHomeApiClient(email="user@example.com", password="secret", session=session)

    await client.async_sign_in()

    assert session.request.await_count == 1
    assert session.request.await_args.kwargs["json"] == {"email": "user@example.com", "password": "secret"}
    assert client._access_token == "access"  # noqa: SLF001
    assert client._refresh_token == "refresh"  # noqa: SLF001
