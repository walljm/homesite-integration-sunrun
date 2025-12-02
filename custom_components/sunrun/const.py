"""Constants for the Sunrun integration."""
from datetime import timedelta

DOMAIN = "sunrun"

# API endpoints
API_BASE_URL = "https://gateway.sunrun.com"
AUTH_REQUEST_ENDPOINT = "/portal-auth/request-passwordless"
AUTH_RESPOND_ENDPOINT = "/portal-auth/respond-passwordless"
CUMULATIVE_PRODUCTION_ENDPOINT = "/performance-api/v1/cumulative-production/daily"
SITE_PRODUCTION_MINUTE_ENDPOINT = "/performance-api/v1/site-production-minute"

# Config keys
CONF_ACCESS_TOKEN = "access_token"
CONF_PROSPECT_ID = "prospect_id"
CONF_PHONE = "phone"
CONF_PTO_DATE = "pto_date"

# Update interval - Sunrun data updates once per day
DEFAULT_SCAN_INTERVAL = timedelta(hours=1)

# Sensor types
SENSOR_TYPES = {
    "daily_production": {
        "name": "Daily Production",
        "unit": "kWh",
        "icon": "mdi:solar-power",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "cumulative_production": {
        "name": "Cumulative Production",
        "unit": "kWh",
        "icon": "mdi:solar-power-variant",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "current_power": {
        "name": "Current Power",
        "unit": "W",
        "icon": "mdi:flash",
        "device_class": "power",
        "state_class": "measurement",
    },
    "consumption": {
        "name": "Consumption",
        "unit": "W",
        "icon": "mdi:home-lightning-bolt",
        "device_class": "power",
        "state_class": "measurement",
    },
    "grid_export": {
        "name": "Grid Export",
        "unit": "W",
        "icon": "mdi:transmission-tower-export",
        "device_class": "power",
        "state_class": "measurement",
    },
    "grid_import": {
        "name": "Grid Import",
        "unit": "W",
        "icon": "mdi:transmission-tower-import",
        "device_class": "power",
        "state_class": "measurement",
    },
    "battery_solar": {
        "name": "Battery Solar",
        "unit": "W",
        "icon": "mdi:battery-charging",
        "device_class": "power",
        "state_class": "measurement",
    },
}
