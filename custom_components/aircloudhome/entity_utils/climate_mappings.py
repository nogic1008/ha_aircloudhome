"""Climate-specific API ↔ Home Assistant value mappings for aircloudhome."""

from __future__ import annotations

from homeassistant.components.climate.const import (
    FAN_AUTO,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_ON,
    SWING_VERTICAL,
    HVACMode,
)

# Preset mode for DRY_COOL — a device-specific mode that has no direct HVACMode equivalent
PRESET_DRY_COOL = "dry_cool"

# Modes in which a humidity setpoint is accepted by the API
HUMIDITY_MODES: frozenset[str] = frozenset({"DRY", "DRY_COOL"})

# Map API modes to Home Assistant HVAC modes
API_MODE_TO_HVAC_MODE: dict[str, HVACMode] = {
    "HEATING": HVACMode.HEAT,
    "COOLING": HVACMode.COOL,
    "DRY": HVACMode.DRY,
    "FAN": HVACMode.FAN_ONLY,
    "AUTO": HVACMode.AUTO,
    "DRY_COOL": HVACMode.DRY,  # Dry Cool - reported as DRY mode; distinguished via preset
    "UNKNOWN": HVACMode.OFF,
}

# Map Home Assistant HVAC modes to API modes
HVAC_MODE_TO_API_MODE: dict[HVACMode, str] = {
    HVACMode.HEAT: "HEATING",
    HVACMode.COOL: "COOLING",
    HVACMode.DRY: "DRY",
    HVACMode.FAN_ONLY: "FAN",
    HVACMode.AUTO: "AUTO",
    HVACMode.OFF: "OFF",
}

# Fan speed mappings (API → HA); reverse derived automatically
API_FAN_SPEED_TO_HA: dict[str, str] = {
    "AUTO": FAN_AUTO,
    "LV1": "level_1",
    "LV2": "level_2",
    "LV3": "level_3",
    "LV4": "level_4",
    "LV5": "level_5",
}
HA_FAN_SPEED_TO_API: dict[str, str] = {v: k for k, v in API_FAN_SPEED_TO_HA.items()}

# Fan swing mappings (API → HA); reverse derived automatically
API_SWING_TO_HA: dict[str, str] = {
    "AUTO": SWING_ON,
    "OFF": SWING_OFF,
    "VERTICAL": SWING_VERTICAL,
    "HORIZONTAL": SWING_HORIZONTAL,
    "BOTH": SWING_BOTH,
}
HA_SWING_TO_API: dict[str, str] = {v: k for k, v in API_SWING_TO_HA.items()}
