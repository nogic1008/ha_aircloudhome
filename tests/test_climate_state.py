"""Tests that climate entities follow the coordinator data."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aircloudhome.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

pytestmark = pytest.mark.integration

_CLIENT = "custom_components.aircloudhome.api.client.AirCloudHomeApiClient"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow Home Assistant to load the integration from custom_components."""


def _unit(**overrides: Any) -> dict[str, Any]:
    """Return an idu-list entry for one indoor unit."""
    return {
        "id": 101,
        "name": "Living room",
        "power": "ON",
        "mode": "COOLING",
        "iduTemperature": 25.0,
        "roomTemperature": 27.0,
        "fanSpeed": "AUTO",
        "fanSwing": "OFF",
        "online": True,
    } | overrides


async def _setup(hass: HomeAssistant, idu_list: AsyncMock) -> tuple[MockConfigEntry, str]:
    """Set up the integration with a mocked API and return the entry and climate entity_id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user-example-com",
        data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"},
    )
    entry.add_to_hass(hass)
    with (
        patch(f"{_CLIENT}.async_get_family_groups", AsyncMock(return_value=[{"familyId": 1}])),
        patch(f"{_CLIENT}.async_get_idu_list", idu_list),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id("climate", DOMAIN, f"{entry.entry_id}_101_climate")
    assert entity_id is not None
    return entry, entity_id


async def _refresh(hass: HomeAssistant, entry: MockConfigEntry, idu_list: AsyncMock) -> None:
    """Run one coordinator poll."""
    with (
        patch(f"{_CLIENT}.async_get_family_groups", AsyncMock(return_value=[{"familyId": 1}])),
        patch(f"{_CLIENT}.async_get_idu_list", idu_list),
    ):
        await entry.runtime_data.coordinator.async_refresh()
        await hass.async_block_till_done()


async def test_unit_offline_at_startup_becomes_available_when_online(hass: HomeAssistant) -> None:
    """A unit that was offline when HA started recovers once the cloud reports it online."""
    idu_list = AsyncMock(return_value=[_unit(online=False)])
    entry, entity_id = await _setup(hass, idu_list)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    idu_list.return_value = [_unit(online=True)]
    await _refresh(hass, entry, idu_list)

    assert hass.states.get(entity_id).state == "cool"


async def test_state_follows_coordinator_updates(hass: HomeAssistant) -> None:
    """Changes made outside HA (app, remote) show up after the next poll."""
    idu_list = AsyncMock(return_value=[_unit()])
    entry, entity_id = await _setup(hass, idu_list)

    idu_list.return_value = [_unit(power="OFF", roomTemperature=24.5)]
    await _refresh(hass, entry, idu_list)

    state = hass.states.get(entity_id)
    assert state.state == "off"
    assert state.attributes["current_temperature"] == 24.5


async def test_unit_missing_from_payload_is_unavailable(hass: HomeAssistant) -> None:
    """A unit that disappears from idu-list is reported unavailable, not stale."""
    idu_list = AsyncMock(return_value=[_unit()])
    entry, entity_id = await _setup(hass, idu_list)

    idu_list.return_value = []
    await _refresh(hass, entry, idu_list)

    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
