# Configuration Reference

This document describes all configuration options and settings available in the Shirokuma AC (aircloudhome) Integration custom integration.

## Integration Configuration

### Initial Setup Options

These options are configured during initial setup via the Home Assistant UI.

#### Credentials

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| **Email** | string | Yes | Your AirCloud Home account email address |
| **Password** | string | Yes | Your account password |

### Options Flow (Reconfiguration)

After initial setup, you can modify settings:

1. Go to **Settings** → **Devices & Services**
2. Find "Shirokuma AC (aircloudhome) Integration"
3. Click **Configure**
4. Modify settings
5. Click **Submit**

**Available options:**

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Update interval (minutes)** | 5 | 1–1440 | How often to poll the cloud API |
| **Enable debug logging** | Off | — | Enable detailed debug logging for troubleshooting |

## Entity Configuration

### Entity Customization

Customize entities via the UI or `configuration.yaml`:

#### Via Home Assistant UI

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find and click the entity
3. Click the settings icon
4. Modify:
   - Entity ID
   - Name
   - Icon
   - Device class (for applicable entities)
   - Area assignment

#### Via configuration.yaml

```yaml
homeassistant:
  customize:
    climate.living_room:
      friendly_name: "Living Room AC"
      icon: mdi:air-conditioner
```

### Disabling Entities

If you don't need certain entities:

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find the entity
3. Click it, then click **Settings** icon
4. Toggle **Enable entity** off

Disabled entities won't update or consume resources.

## Services

This integration does not provide custom services. Use the standard Home Assistant climate services:

### `climate.set_hvac_mode`

Set the operating mode.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | Target climate entity |
| `hvac_mode` | string | `heat`, `cool`, `dry`, `fan_only`, `auto`, `off` |

### `climate.set_temperature`

Set the target temperature (16–32°C, 0.5°C increments).

### `climate.set_fan_mode`

Set the fan speed: `auto`, `level_1`, `level_2`, `level_3`, `level_4`, `level_5`.

### `climate.set_swing_mode`

Set the swing direction: `off`, `vertical`, `horizontal`, `both`, `on`.

### `climate.turn_on` / `climate.turn_off`

Power the AC unit on or off.

**Example — set temperature via automation:**

```yaml
automation:
  - alias: "Preheat before arriving home"
    trigger:
      - trigger: time
        at: "17:30:00"
    action:
      - action: climate.set_temperature
        target:
          entity_id: climate.living_room
        data:
          temperature: 22
```

## Advanced Configuration

### Multiple Instances (Multiple Accounts)

You can add multiple instances of this integration for different accounts:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Shirokuma AC (aircloudhome) Integration"
4. Configure with different account credentials

Each instance creates separate entities for all AC units under that account. AC units within a single account (across multiple family groups) are all handled by a single config entry.

### Polling Behavior

The integration polls the AirCloud Home cloud API to fetch updates. State changes are **not real-time**.

- **Default interval:** 5 minutes
- **Range:** 1–1440 minutes (1 minute to 24 hours)

Adjust the update interval in **Configure** → **Update interval (minutes)**:

- Shorter intervals provide more responsive state updates but increase API requests
- Longer intervals reduce API load but delay state reflection

## Diagnostic Data

Diagnostic data is collected from the device API response and includes:

- Device state (power, mode, temperatures, fan speed, swing)
- Online status
- Last update timestamp

**Privacy note:** Diagnostic data may contain account information. Review before sharing.

## Troubleshooting Configuration

### Config Entry Fails to Load

If the integration fails to load after configuration:

1. Check Home Assistant logs for errors
2. Verify your email and password are correct
3. Ensure internet connectivity is available
4. Try removing and re-adding the integration

### Options Don't Save

If configuration changes aren't persisted:

1. Check for validation errors in the UI
2. Ensure values are within allowed ranges
3. Review logs for detailed error messages
4. Try restarting Home Assistant

## Related Documentation

- [Getting Started](./GETTING_STARTED.md) - Installation and initial setup
- [GitHub Issues](https://github.com/nogic1008/ha_aircloudhome/issues) - Report problems
