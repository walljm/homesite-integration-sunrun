"""Constants for the Sunrun integration."""
from datetime import timedelta

DOMAIN = "sunrun"

# API endpoints
API_BASE_URL = "https://gateway.sunrun.com"
AUTH_REQUEST_ENDPOINT = "/portal-auth/request-passwordless"
AUTH_RESPOND_ENDPOINT = "/portal-auth/respond-passwordless"
CUMULATIVE_PRODUCTION_ENDPOINT = "/performance-api/v1/cumulative-production/daily"
SITE_PRODUCTION_MINUTE_ENDPOINT = "/performance-api/v1/site-production-minute"
PRODUCT_OFFERINGS_ENDPOINT = "/performance-api/v1/product-offerings"

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
    "system_size": {
        "name": "System Size",
        "unit": "kW",
        "icon": "mdi:solar-panel-large",
        "device_class": None,
        "state_class": None,
    },
    "num_panels": {
        "name": "Number of Panels",
        "unit": None,
        "icon": "mdi:solar-panel",
        "device_class": None,
        "state_class": None,
    },
    "system_azimuth": {
        "name": "System Azimuth",
        "unit": "°",
        "icon": "mdi:compass",
        "device_class": None,
        "state_class": None,
    },
    "system_pitch": {
        "name": "System Pitch",
        "unit": "°",
        "icon": "mdi:angle-acute",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_jan": {
        "name": "Sun Exposure January",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_feb": {
        "name": "Sun Exposure February",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_mar": {
        "name": "Sun Exposure March",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_apr": {
        "name": "Sun Exposure April",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_may": {
        "name": "Sun Exposure May",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_jun": {
        "name": "Sun Exposure June",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_jul": {
        "name": "Sun Exposure July",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_aug": {
        "name": "Sun Exposure August",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_sep": {
        "name": "Sun Exposure September",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_oct": {
        "name": "Sun Exposure October",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_nov": {
        "name": "Sun Exposure November",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
    "sun_exposure_dec": {
        "name": "Sun Exposure December",
        "unit": "%",
        "icon": "mdi:weather-sunny",
        "device_class": None,
        "state_class": None,
    },
}
