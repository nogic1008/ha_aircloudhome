# Shirokuma AC (aircloudhome) Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

<!--
Uncomment and customize these badges if you want to use them:

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]
[![Discord][discord-shield]][discord]
-->

**✨ Develop in the cloud:** Want to contribute or customize this integration? Open it directly in GitHub Codespaces - no local setup required!

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/nogic1008/ha_aircloudhome?quickstart=1)

## ✨ Features

- **Easy Setup**: Simple configuration through the UI - no YAML required
- **Full AC Control**: Power on/off, operating mode, target temperature, fan speed, swing direction
- **Polled Status**: Current room temperature and device state, updated at a configurable interval (default: 5 minutes)
- **Reconfigurable**: Change credentials anytime without removing the integration
- **Options Flow**: Adjust settings like update interval after setup
- **Multiple Units**: Supports multiple AC units across multiple family groups

> **🛠️ Tested hardware:** Hitachi RAS-X40L2. Other **room air conditioners (RAC)** connected via AirCloud Home should work. Packaged air conditioners (PAC) use a separate API and are not supported.

**This integration will set up the following platforms.**

Platform | Description
-- | --
`climate` | Air conditioning control (power, mode, temperature, fan speed, swing)

## 🚀 Quick Start

### Step 1: Install the Integration

**Prerequisites:** This integration requires [HACS](https://hacs.xyz/) (Home Assistant Community Store) to be installed.

Click the button below to open the integration directly in HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=nogic1008&repository=ha_aircloudhome&category=integration)

Then:

1. Click "Download" to install the integration
2. **Restart Home Assistant** (required after installation)

> **Note:** The My Home Assistant redirect will first take you to a landing page. Click the button there to open your Home Assistant instance.

<details>
<summary>**Manual Installation (Advanced)**</summary>

If you prefer not to use HACS:

1. Download the `custom_components/aircloudhome/` folder from this repository
2. Copy it to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

</details>

### Step 2: Add and Configure the Integration

**Important:** You must have installed the integration first (see Step 1) and restarted Home Assistant!

#### Option 1: One-Click Setup (Quick)

Click the button below to open the configuration dialog:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=aircloudhome)

Follow the setup wizard:

1. Enter your email address
2. Enter your password
3. Click Submit

That's it! The integration will start loading your data.

#### Option 2: Manual Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for "Shirokuma AC (aircloudhome) Integration"
4. Follow the same setup steps as Option 1

### Step 3: Adjust Settings (Optional)

After setup, you can adjust options:

1. Go to **Settings** → **Devices & Services**
2. Find **Shirokuma AC (aircloudhome) Integration**
3. Click **Configure** to adjust:
   - Update interval (how often to refresh data)
   - Enable debug logging

You can also **Reconfigure** your credentials anytime without removing the integration.

### Step 4: Start Using!

The integration creates climate entities for each of your AC units:

- **Climate**: Full AC control — power, mode (heat/cool/dry/fan/auto), target temperature, fan speed, swing direction
- Current room temperature is shown as the current temperature on each climate entity

Find all entities in **Settings** → **Devices & Services** → **Shirokuma AC (aircloudhome) Integration** → click on the device.

## Available Entities

### Climate

One climate entity is created per AC unit:

- **HVAC Modes**: Heat, Cool, Dry, Fan Only, Auto, Off
- **Temperature**: Set target temperature (16–32°C, 0.5°C increments)
- **Fan Speed**: auto, level_1, level_2, level_3, level_4, level_5
- **Swing Mode**: off, vertical, horizontal, both, on (auto)
- **Current Temperature**: Room temperature reported by the unit

## Configuration Options

### During Setup

Name | Required | Description
-- | -- | --
Email | Yes | Your AirCloud Home account email address
Password | Yes | Your account password

### After Setup (Options)

You can change these anytime by clicking **Configure**:

Name | Default | Description
-- | -- | --
Update Interval | 5 minutes | How often to poll the AirCloud Home cloud API (1–1440 minutes)
Enable Debugging | Off | Enable extra debug logging

> **Note:** State updates are not real-time. The integration polls the cloud API at the configured interval. For most use cases the default 5-minute interval is sufficient. Setting a shorter interval increases API requests; setting a longer interval reduces responsiveness.

## Troubleshooting

### Authentication Issues

#### Reauthentication

If your credentials expire or change, Home Assistant will automatically prompt you to reauthenticate:

1. Go to **Settings** → **Devices & Services**
2. Look for **"Action Required"** or **"Configuration Required"** message on the integration
3. Click **"Reconfigure"** or follow the prompt
4. Enter your updated email and password
5. Click Submit

The integration will automatically resume normal operation with the new credentials.

#### Manual Credential Update

You can also update credentials at any time without waiting for an error:

1. Go to **Settings** → **Devices & Services**
2. Find **Shirokuma AC (aircloudhome) Integration**
3. Click the **3 dots menu** → **Reconfigure**
4. Enter new email/password
5. Click Submit

### Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.aircloudhome: debug
```

### Common Issues

#### Authentication Errors

If you receive authentication errors:

1. Verify your email and password are correct
2. Check that your account has the necessary permissions
3. Wait for the automatic reauthentication prompt, or manually reconfigure

#### Device Not Responding

If your AC unit shows as unavailable:

1. Check your internet connection (this integration uses the AirCloud Home cloud API)
2. Verify the AC unit is powered on and connected
3. Try reloading the integration

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request if you have suggestions or improvements.

### 🛠️ Development Setup

Want to contribute or customize this integration? You have two options:

#### Cloud Development (Recommended)

The easiest way to get started - develop directly in your browser with GitHub Codespaces:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/nogic1008/ha_aircloudhome?quickstart=1)

- ✅ Zero local setup required
- ✅ Pre-configured development environment
- ✅ Home Assistant included for testing
- ✅ 60 hours/month free for personal accounts

#### Local Development

Prefer working on your machine? You'll need:

- Docker Desktop
- VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Then:

1. Clone this repository
2. Open in VS Code
3. Click "Reopen in Container" when prompted

Both options give you the same fully-configured development environment with Home Assistant, Python 3.13, and all necessary tools.

---

## 🤖 AI-Assisted Development

> **ℹ️ Transparency Notice**
>
> This integration was developed with assistance from AI coding agents (GitHub Copilot, Claude, and others). While the codebase follows Home Assistant Core standards, AI-generated code may not be reviewed or tested to the same extent as manually written code.
>
> AI tools were used to:
>
> - Generate boilerplate code following Home Assistant patterns
> - Implement standard integration features (config flow, coordinator, entities)
> - Ensure code quality and type safety
> - Write documentation and comments
>
> Please be aware that AI-assisted development may result in unexpected behavior or edge cases that haven't been thoroughly tested. If you encounter any issues, please [open an issue](../../issues) on GitHub.
>
> *Note: This section can be removed or modified if AI assistance was not used in your integration's development.*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [@nogic1008][user_profile]**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/nogic1008/ha_aircloudhome.svg?style=for-the-badge
[commits]: https://github.com/nogic1008/ha_aircloudhome/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/nogic1008/ha_aircloudhome.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40nogic1008-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/nogic1008/ha_aircloudhome.svg?style=for-the-badge
[releases]: https://github.com/nogic1008/ha_aircloudhome/releases
[user_profile]: https://github.com/nogic1008

<!-- Optional badge definitions - uncomment if needed:
[buymecoffee]: https://www.buymeacoffee.com/nogic1008
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
-->
