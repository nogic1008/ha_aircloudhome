"""
Base entity class for aircloudhome.

This module provides the base entity class that all integration entities inherit from.
It handles common functionality like device info, unique IDs, and coordinator integration.

For more information on entities:
https://developers.home-assistant.io/docs/core/entity
https://developers.home-assistant.io/docs/core/entity/index/#common-properties
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.aircloudhome.const import ATTRIBUTION
from custom_components.aircloudhome.coordinator import AirCloudHomeDataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class AirCloudHomeEntity(CoordinatorEntity[AirCloudHomeDataUpdateCoordinator]):
    """
    Base entity class for aircloudhome.

    All entities in this integration inherit from this class, which provides:
    - Automatic coordinator updates
    - Device info management
    - Unique ID generation
    - Attribution and naming conventions

    For more information:
    https://developers.home-assistant.io/docs/core/entity
    https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    """

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AirCloudHomeDataUpdateCoordinator,
        entity_description: EntityDescription,
        device_id: str | None = None,
    ) -> None:
        """
        Initialize the base entity.

        Args:
            coordinator: The data update coordinator for this entity.
            entity_description: The entity description defining characteristics.
            device_id: Optional device ID for multi-device support (e.g., AC unit ID).

        """
        super().__init__(coordinator)
        self.entity_description = entity_description

        # Generate unique ID with optional device ID
        if device_id is not None:
            self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{device_id}_{entity_description.key}"
        else:
            self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

    def _get_device_info(self) -> DeviceInfo:
        """
        Get device information for this entity.

        Override this method in subclasses to customize device info per entity type.

        Returns:
            DeviceInfo for the device associated with this entity.
        """
        return DeviceInfo(
            identifiers={
                (
                    self.coordinator.config_entry.domain,
                    self.coordinator.config_entry.entry_id,
                ),
            },
            name=self.coordinator.config_entry.title,
            manufacturer=self.coordinator.config_entry.domain,
            model=self.coordinator.data.get("model", "Unknown"),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return self._get_device_info()
