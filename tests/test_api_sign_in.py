"""Tests for signing in to the AirCloud Home API."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.aircloudhome.api import (
    AirCloudHomeApiClient,
    AirCloudHomeApiClientAccountLockedError,
    AirCloudHomeApiClientAuthenticationError,
)

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


async def test_sign_in_on_locked_account_raises_account_locked_error() -> None:
    """A 423 SOFT_LOCK is reported as a lock, not as wrong credentials, without retrying."""
    session = _session(423, {"errorState": "SOFT_LOCK"})
    client = AirCloudHomeApiClient(email="user@example.com", password="secret", session=session)

    with pytest.raises(AirCloudHomeApiClientAccountLockedError) as exc_info:
        await client.async_sign_in()

    assert not isinstance(exc_info.value, AirCloudHomeApiClientAuthenticationError)
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


async def test_sign_in_does_not_log_credentials(caplog: pytest.LogCaptureFixture) -> None:
    """Debug logs (often attached to issues) never contain the email or password."""
    session = _session(200, {"token": "access", "refreshToken": "refresh"})
    client = AirCloudHomeApiClient(email="user@example.com", password="s3cret-pass", session=session)

    with caplog.at_level(logging.DEBUG, logger="custom_components.aircloudhome.api.client"):
        await client.async_sign_in()

    assert "/iam/auth/sign-in" in caplog.text
    assert "user@example.com" not in caplog.text
    assert "s3cret-pass" not in caplog.text
