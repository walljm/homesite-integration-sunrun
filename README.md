# Sunrun Solar Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration to monitor your Sunrun solar system using data from the [my.sunrun.com](https://my.sunrun.com) portal.

## Features

- **Solar Production Monitoring**: Track your daily and cumulative solar energy production
- **Real-time Power**: View current power generation (updated hourly)
- **Energy Flow** (if available on your system):
  - Grid export/import
  - Home consumption
  - Battery solar contribution

## Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| Daily Production | Energy produced today | kWh |
| Cumulative Production | Total energy produced since installation | kWh |
| Current Power | Current power being generated | W |
| Consumption | Current home power consumption | W |
| Grid Export | Power being exported to the grid | W |
| Grid Import | Power being imported from the grid | W |
| Battery Solar | Power from battery | W |

> **Note**: Not all sensors may be available depending on your Sunrun system configuration. Systems without consumption monitoring or batteries will show those sensors as unavailable.

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Go to **HACS** → **Integrations** → **⋮** (menu) → **Custom repositories**
3. Add this repository URL: `https://github.com/walljm/homesite-integration-sunrun`
4. Select **Integration** as the category
5. Click **Add**
6. Search for "Sunrun" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/walljm/homesite-integration-sunrun/releases)
2. Extract the `sunrun` folder from the zip file
3. Copy the `sunrun` folder to your `config/custom_components/` directory
4. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Sunrun"
3. Enter the phone number associated with your Sunrun account
4. You'll receive an SMS with a 6-digit verification code
5. Enter the code to complete setup

## How It Works

This integration uses the unofficial Sunrun API (the same one used by my.sunrun.com). Authentication is done via SMS one-time password (OTP) - the same flow you use when logging into the Sunrun portal.

### Data Updates

- Data is refreshed every **1 hour**
- Sunrun's backend typically updates production data **once per day**
- Real-time power readings may have a 15-minute delay

### Authentication

- Uses SMS-based passwordless authentication
- Access tokens are stored securely in Home Assistant
- If the token expires, you'll be prompted to re-authenticate

## Troubleshooting

### "Authentication expired" error

Your Sunrun access token has expired. Go to the integration and click "Reconfigure" to re-authenticate.

### Sensors showing "Unavailable"

Some sensors (consumption, grid import/export, battery) are only available on systems with the appropriate hardware. If you don't have consumption monitoring or a battery, these sensors will be unavailable.

### No data showing

- Ensure your Sunrun system is operational
- Check that you can see data on [my.sunrun.com](https://my.sunrun.com)
- Data may take up to 24 hours to appear after initial setup

## Disclaimer

This is an **unofficial** integration that uses reverse-engineered APIs. Sunrun may change their API at any time without notice, which could break this integration. Use at your own risk.

This integration is not affiliated with, endorsed by, or connected to Sunrun Inc.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
