"""Tests for the AirCloud Home config flow region handling."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aircloudhome.const import CONF_REGION, DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

pytestmark = pytest.mark.integration

_VALIDATE = "custom_components.aircloudhome.config_flow_handler.config_flow.validate_credentials"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow Home Assistant to load the integration from custom_components."""


@pytest.fixture
def validate_credentials() -> Iterator[AsyncMock]:
    """Accept any credentials and skip setting up the created entry."""
    with (
        patch(_VALIDATE, new_callable=AsyncMock) as validate,
        patch("custom_components.aircloudhome.async_setup_entry", return_value=True),
    ):
        yield validate


async def test_user_step_stores_selected_region(hass: HomeAssistant, validate_credentials: AsyncMock) -> None:
    """The region chosen during setup is validated against and stored."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_REGION: "global", CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_REGION] == "global"
    assert validate_credentials.await_args.kwargs["region"] == "global"


async def test_user_step_defaults_to_japan(hass: HomeAssistant, validate_credentials: AsyncMock) -> None:
    """Japan stays the default so the form behaves as before for existing users."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_REGION] == "japan"


async def test_reauth_uses_region_of_existing_entry(hass: HomeAssistant, validate_credentials: AsyncMock) -> None:
    """Reauthentication validates against the region the entry was set up with."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user-example-com",
        data={CONF_REGION: "global", CONF_USERNAME: "user@example.com", CONF_PASSWORD: "old"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "new"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert validate_credentials.await_args.kwargs["region"] == "global"
    assert entry.data[CONF_REGION] == "global"
    assert entry.data[CONF_PASSWORD] == "new"


async def test_reauth_of_legacy_entry_uses_japan(hass: HomeAssistant, validate_credentials: AsyncMock) -> None:
    """Entries created before region support keep using the Japan API."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user-example-com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "old"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "new"},
    )

    assert validate_credentials.await_args.kwargs["region"] == "japan"
