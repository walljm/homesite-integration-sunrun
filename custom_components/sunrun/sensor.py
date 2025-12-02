"""Sensor platform for Sunrun integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import SunrunDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sunrun sensors based on a config entry."""
    coordinator: SunrunDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(SunrunSensor(coordinator, entry, sensor_type))

    async_add_entities(sensors)


class SunrunSensor(CoordinatorEntity[SunrunDataUpdateCoordinator], SensorEntity):
    """Representation of a Sunrun sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunrunDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{entry.data['prospect_id']}_{sensor_type}"
        
        sensor_info = SENSOR_TYPES[sensor_type]
        self._attr_name = sensor_info["name"]
        self._attr_icon = sensor_info["icon"]
        
        # Set unit of measurement
        unit = sensor_info.get("unit")
        if unit:
            self._attr_native_unit_of_measurement = unit
        
        # Set device class
        device_class = sensor_info.get("device_class")
        if device_class == "energy":
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        elif device_class == "power":
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_native_unit_of_measurement = UnitOfPower.WATT
        
        # Set state class
        state_class = sensor_info.get("state_class")
        if state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Device info - will be enhanced with system data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["prospect_id"])},
            name="Sunrun Solar System",
            manufacturer="Sunrun",
            model="Solar System",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        
        value = self.coordinator.data.get(self._sensor_type)
        
        # Round to reasonable precision
        if value is not None:
            if self._sensor_type in ("daily_production", "monthly_production", "lifetime_production"):
                return round(value, 2)
            else:
                return round(value, 0)
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {}
        
        if self.coordinator.data:
            last_update = self.coordinator.data.get("last_update")
            if last_update:
                attrs["last_api_update"] = last_update
            
            # Add system info as attributes for main sensors
            if self._sensor_type in ("daily_production", "cumulative_production", "current_power"):
                pto_date = self.coordinator.data.get("pto_date")
                if pto_date:
                    attrs["pto_date"] = pto_date
                
                has_battery = self.coordinator.data.get("has_battery")
                if has_battery is not None:
                    attrs["has_battery"] = has_battery
                
                has_consumption = self.coordinator.data.get("has_consumption")
                if has_consumption is not None:
                    attrs["has_consumption_monitoring"] = has_consumption
        
        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        
        # Check if we have data for this specific sensor
        if self.coordinator.data is None:
            return False
        
        # Some sensors might not be available for all systems
        value = self.coordinator.data.get(self._sensor_type)
        
        # For power sensors and optional features, None means not available
        if self._sensor_type in ("consumption", "grid_export", "grid_import", "battery_solar"):
            return value is not None
        
        # System info sensors should always be available if we have data
        if self._sensor_type in ("system_size", "num_panels", "system_azimuth", "system_pitch") or self._sensor_type.startswith("sun_exposure_"):
            return value is not None
        
        return True
