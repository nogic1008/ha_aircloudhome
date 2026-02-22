# Getting Started with Shirokuma AC (aircloudhome) Integration

This guide will help you install and set up the Shirokuma AC (aircloudhome) Integration custom integration for Home Assistant.

## Prerequisites

- Home Assistant 2025.7.0 or newer
- HACS (Home Assistant Community Store) installed
- AirCloud Home account (email and password)

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/nogic1008/ha_aircloudhome`
6. Set category to "Integration"
7. Click "Add"
8. Find "Shirokuma AC (aircloudhome) Integration" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/nogic1008/ha_aircloudhome/releases)
2. Extract the `aircloudhome` folder from the archive
3. Copy it to `custom_components/aircloudhome/` in your Home Assistant configuration directory
4. Restart Home Assistant

## Initial Setup

After installation, add the integration:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Shirokuma AC (aircloudhome) Integration"
4. Follow the configuration steps:

### Step 1: Credentials

Enter your AirCloud Home account details:

- **Email:** Your AirCloud Home account email address
- **Password:** Your account password

Click **Submit** to verify credentials.

## What Gets Created

After successful setup, the integration creates:

### Devices

One device per AC unit, identified by its `id` (numeric device ID). Each device shows:

- Manufacturer (from the unit's model field)
- Serial number
- Hardware version (`vendorThingId`)

### Entities

#### Climate

- `climate.<room_name>` — Full AC control per unit
  - HVAC modes: heat, cool, dry, fan only, auto, off
  - Temperature range: 16–32°C (0.5°C increments)
  - Fan speeds: auto, level_1, level_2, level_3, level_4, level_5
  - Swing modes: off, vertical, horizontal, both, on

## First Steps

### Dashboard Cards

Add entities to your dashboard:

1. Go to your dashboard
2. Click **Edit Dashboard** → **Add Card**
3. Choose card type (e.g., "Entities", "Glance")
4. Select entities from "Shirokuma AC (aircloudhome) Integration"

Example climate card:

```yaml
type: thermostat
entity: climate.living_room
```

### Automations

Use the integration in automations:

**Example - Set AC temperature at a schedule:**

```yaml
automation:
  - alias: "Set AC to 26°C at night"
    trigger:
      - trigger: time
        at: "22:00:00"
    action:
      - action: climate.set_temperature
        target:
          entity_id: climate.living_room
        data:
          temperature: 26
```

**Example - Turn off all AC units when leaving:**

```yaml
automation:
  - alias: "Turn off AC on leaving"
    trigger:
      - trigger: state
        entity_id: person.my_person
        to: not_home
    action:
      - action: climate.turn_off
        target:
          entity_id: climate.living_room
```

## Troubleshooting

### Connection Failed

If setup fails with authentication errors:

1. Verify your email address is correct
2. Check that your password is correct
3. Ensure your AirCloud Home account is active
4. Check Home Assistant logs for detailed error messages

### Entities Not Updating

If entities show "Unavailable" or don't update:

1. Check that the AC unit is powered on and online
2. Verify internet connectivity (this integration uses the AirCloud Home cloud API)
3. Verify credentials haven't expired
4. Review logs: **Settings** → **System** → **Logs**
5. Try reloading the integration

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: warning
  logs:
    custom_components.aircloudhome: debug
```

Add this to `configuration.yaml`, restart, and reproduce the issue. Check logs for detailed information.

## Next Steps

- See [CONFIGURATION.md](./CONFIGURATION.md) for detailed configuration options
- Report issues at [GitHub Issues](https://github.com/nogic1008/ha_aircloudhome/issues)

## Support

For help and discussion:

- [GitHub Discussions](https://github.com/nogic1008/ha_aircloudhome/discussions)
- [Home Assistant Community Forum](https://community.home-assistant.io/)
