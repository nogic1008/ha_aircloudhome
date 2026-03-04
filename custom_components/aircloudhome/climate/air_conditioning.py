"""Climate entity for aircloudhome AC devices."""

from __future__ import annotations

from typing import Any

from custom_components.aircloudhome.coordinator import AirCloudHomeDataUpdateCoordinator
from custom_components.aircloudhome.entity import AirCloudHomeEntity
from custom_components.aircloudhome.entity_utils.climate_mappings import (
    API_FAN_SPEED_TO_HA,
    API_MODE_TO_HVAC_MODE,
    API_SWING_TO_HA,
    HA_FAN_SPEED_TO_API,
    HA_SWING_TO_API,
    HUMIDITY_MODES,
    HVAC_MODE_TO_API_MODE,
    PRESET_DRY_COOL,
)
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import PRESET_NONE, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

# Climate entity description for AC units
CLIMATE_ENTITY_DESCRIPTION = EntityDescription(
    key="climate",
    name="Room Air Conditioner",
    translation_key="room_air_conditioner",
)


class AirCloudHomeAirConditioner(ClimateEntity, AirCloudHomeEntity):
    """Climate entity for AirCloud Home AC device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16.0
    _attr_max_temp = 32.0
    _attr_target_temperature_step = 0.5
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_hvac_modes = [
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.AUTO,
        HVACMode.OFF,
    ]
    _attr_fan_modes = list(API_FAN_SPEED_TO_HA.values())
    _attr_swing_modes = list(API_SWING_TO_HA.values())
    _attr_preset_modes = [PRESET_NONE, PRESET_DRY_COOL]

    def __init__(
        self,
        coordinator: AirCloudHomeDataUpdateCoordinator,
        entity_description: EntityDescription,
        device: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, entity_description, device_id=str(device["id"]))
        self._device = device
        self._supports_humidity = "humidity" in device
        if self._supports_humidity:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
            self._attr_min_humidity = 40
            self._attr_max_humidity = 60

    def _get_device_info(self) -> DeviceInfo:
        """Get device information for this AC unit."""
        return DeviceInfo(
            identifiers={("aircloudhome", f"{self.coordinator.config_entry.entry_id}_{self._device['id']}")},
            name=self._device.get("name", f"AC Unit {self._device['id']}"),
            manufacturer=self._device.get("model"),
            serial_number=self._device.get("serialNumber"),
            hw_version=self._device.get("vendorThingId"),
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device.get("online", False)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._device.get("roomTemperature")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._device.get("iduTemperature")

    @property
    def target_humidity(self) -> int | None:
        """Return the target humidity."""
        return self._device.get("humidity")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if self._device.get("power") == "OFF":
            return HVACMode.OFF

        api_mode = self._device.get("mode", "UNKNOWN")
        return API_MODE_TO_HVAC_MODE.get(api_mode, HVACMode.OFF)

    @property
    def fan_mode(self) -> str | None:
        """Return the fan mode."""
        api_speed = self._device.get("fanSpeed", "AUTO")
        return API_FAN_SPEED_TO_HA.get(api_speed, "auto")

    @property
    def swing_mode(self) -> str | None:
        """Return the swing mode."""
        api_swing = self._device.get("fanSwing", "OFF")
        return API_SWING_TO_HA.get(api_swing, "off")

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode."""
        if self._device.get("power") == "ON" and self._device.get("mode") == "DRY_COOL":
            return PRESET_DRY_COOL
        return PRESET_NONE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # Round to nearest 0.5
        temperature = round(temperature * 2) / 2

        await self._async_update_device(idu_temperature=temperature)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._async_update_device(power="OFF")
        else:
            api_mode = HVAC_MODE_TO_API_MODE.get(hvac_mode, "AUTO")
            await self._async_update_device(power="ON", mode=api_mode)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        api_speed = HA_FAN_SPEED_TO_API.get(fan_mode, "AUTO")
        await self._async_update_device(fan_speed=api_speed)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        api_swing = HA_SWING_TO_API.get(swing_mode, "OFF")
        await self._async_update_device(fan_swing=api_swing)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode == PRESET_DRY_COOL:
            await self._async_update_device(power="ON", mode="DRY_COOL")
        elif preset_mode == PRESET_NONE and self._device.get("mode") == "DRY_COOL":
            # Fall back to DRY when clearing the DRY_COOL preset
            await self._async_update_device(mode="DRY")

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        if not self._supports_humidity:
            return

        humidity_value = max(self._attr_min_humidity, min(self._attr_max_humidity, float(humidity)))
        # Round to nearest 5
        humidity_target = int(round(humidity_value / 5) * 5)
        await self._async_update_device(humidity=humidity_target)

    async def async_turn_on(self) -> None:
        """Turn on the AC."""
        await self._async_update_device(power="ON")

    async def async_turn_off(self) -> None:
        """Turn off the AC."""
        await self._async_update_device(power="OFF")

    async def _async_update_device(
        self,
        power: str | None = None,
        mode: str | None = None,
        fan_speed: str | None = None,
        fan_swing: str | None = None,
        idu_temperature: float | None = None,
        humidity: int | None = None,
    ) -> None:
        """Update device state through the API."""
        # Use current values for parameters not being updated
        current_power = self._device.get("power", "ON")
        current_mode = self._device.get("mode", "AUTO")
        current_fan_speed = self._device.get("fanSpeed", "AUTO")
        current_fan_swing = self._device.get("fanSwing", "OFF")
        current_temp = self._device.get("iduTemperature", 22.0)
        # humidity is the target humidity setpoint retrieved from the device, not the measured room humidity.
        target_humidity_raw = self._device.get("humidity")
        target_humidity_setpoint = (
            int(round(target_humidity_raw)) if isinstance(target_humidity_raw, (int, float)) else None
        )

        effective_power = power or current_power
        effective_mode = mode or current_mode
        # humidity is only valid for DRY / DRY_COOL modes; sending it in other modes causes a 400 error
        resolved_humidity = (
            (humidity if humidity is not None else target_humidity_setpoint)
            if effective_power == "ON" and effective_mode in HUMIDITY_MODES
            else None
        )

        try:
            await self.coordinator.config_entry.runtime_data.client.async_control_device(
                rac_id=self._device["id"],
                family_id=self._device["familyId"],
                power=effective_power,
                mode=effective_mode,
                fan_speed=fan_speed or current_fan_speed,
                fan_swing=fan_swing or current_fan_swing,
                idu_temperature=idu_temperature if idu_temperature is not None else current_temp,
                humidity=resolved_humidity,
            )

            # Update local state immediately for responsiveness
            if power is not None:
                self._device["power"] = power
            if mode is not None:
                self._device["mode"] = mode
            if fan_speed is not None:
                self._device["fanSpeed"] = fan_speed
            if fan_swing is not None:
                self._device["fanSwing"] = fan_swing
            if idu_temperature is not None:
                self._device["iduTemperature"] = idu_temperature
            if humidity is not None:
                self._device["humidity"] = humidity

            self.async_write_ha_state()

            # Refresh data from coordinator
            await self.coordinator.async_request_refresh()

        except Exception:
            self._attr_available = False
            self.async_write_ha_state()
            raise
