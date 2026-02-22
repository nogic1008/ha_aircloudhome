"""Climate platform for aircloudhome."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .air_conditioning import CLIMATE_ENTITY_DESCRIPTION, AirCloudHomeAirConditioner

if TYPE_CHECKING:
    from custom_components.aircloudhome.data import AirCloudHomeConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AirCloudHomeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    coordinator = entry.runtime_data.coordinator

    # Create climate entities for each AC device
    devices = coordinator.data.get("devices", [])
    async_add_entities(
        AirCloudHomeAirConditioner(
            coordinator=coordinator,
            entity_description=CLIMATE_ENTITY_DESCRIPTION,
            device=device,
        )
        for device in devices
    )
