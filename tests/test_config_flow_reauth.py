"""Tests for the AirCloud Home reauthentication flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aircloudhome.api import AirCloudHomeApiClientAuthenticationError
from custom_components.aircloudhome.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

pytestmark = pytest.mark.integration

_VALIDATE = "custom_components.aircloudhome.config_flow_handler.config_flow.validate_credentials"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow Home Assistant to load the integration from custom_components."""


async def test_reauth_form_names_the_account(hass: HomeAssistant) -> None:
    """The reauth description receives the {email} placeholder it renders."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user-example-com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "old"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"]["email"] == "user@example.com"


async def test_reauth_with_wrong_password_shows_auth_error(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Expected validation failures map to a form error and a one-line warning."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user-example-com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "old"},
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)

    with patch(_VALIDATE, AsyncMock(side_effect=AirCloudHomeApiClientAuthenticationError("Invalid credentials"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "wrong"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}
    assert "Could not validate credentials: Invalid credentials" in caplog.text
    assert "Traceback" not in caplog.text


async def test_unexpected_validation_error_is_logged_with_traceback(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Unknown failures map to the generic error and keep their traceback in the log."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user-example-com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "old"},
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)

    with patch(_VALIDATE, AsyncMock(side_effect=KeyError("token"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"},
        )

    assert result["errors"] == {"base": "unknown"}
    assert "Unexpected error while validating credentials" in caplog.text
    assert "KeyError: 'token'" in caplog.text
