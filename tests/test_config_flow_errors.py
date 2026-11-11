"""Tests for the errors shown by the AirCloud Home config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.aircloudhome.api import (
    AirCloudHomeApiClientAccountLockedError,
    AirCloudHomeApiClientAuthenticationError,
    AirCloudHomeApiClientCommunicationError,
)
from custom_components.aircloudhome.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

pytestmark = pytest.mark.integration

_VALIDATE = "custom_components.aircloudhome.config_flow_handler.config_flow.validate_credentials"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow Home Assistant to load the integration from custom_components."""


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (AirCloudHomeApiClientAuthenticationError("Invalid credentials"), "auth"),
        (AirCloudHomeApiClientAccountLockedError("locked"), "account_locked"),
        (AirCloudHomeApiClientCommunicationError("timeout"), "connection"),
    ],
)
async def test_user_step_maps_validation_errors(hass: HomeAssistant, exception: Exception, error: str) -> None:
    """Each sign-in failure is shown with its own message on the setup form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    with patch(_VALIDATE, AsyncMock(side_effect=exception)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
