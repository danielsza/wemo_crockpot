"""Sensor platform for WeMo Crockpot."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WeMo Crockpot sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device = data["device"]

    async_add_entities(
        [
            CrockpotModeSensor(coordinator, device, entry),
            CrockpotRemainingTimeSensor(coordinator, device, entry),
            CrockpotRemainingTimeHoursSensor(coordinator, device, entry),
            CrockpotRemainingTimeMinutesSensor(coordinator, device, entry),
            CrockpotCookedTimeSensor(coordinator, device, entry),
        ]
    )


class CrockpotSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Crockpot sensors."""

    def __init__(self, coordinator, device, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.serial_number)},
            "name": f"WeMo Crockpot",
            "manufacturer": "Belkin",
            "model": "Crockpot",
        }


class CrockpotModeSensor(CrockpotSensorBase):
    """Sensor for the current cooking mode."""

    _attr_name = "Mode Status"
    _attr_icon = "mdi:pot-steam"

    def __init__(self, coordinator, device, entry):
        """Initialize the mode sensor."""
        super().__init__(coordinator, device, entry)
        self._attr_unique_id = f"{device.serial_number}_mode_status"

    @property
    def native_value(self) -> str:
        """Return the current mode."""
        return self.coordinator.data.get("mode_string", "Unknown")


class CrockpotRemainingTimeSensor(CrockpotSensorBase):
    """Sensor for remaining cooking time."""

    _attr_name = "Remaining Time"
    _attr_icon = "mdi:timer-sand"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator, device, entry):
        """Initialize the remaining time sensor."""
        super().__init__(coordinator, device, entry)
        self._attr_unique_id = f"{device.serial_number}_remaining_time"

    @property
    def native_value(self) -> int:
        """Return the remaining time in minutes."""
        return self.coordinator.data.get("remaining_time", 0)


class CrockpotRemainingTimeHoursSensor(CrockpotSensorBase):
    """Sensor for remaining cooking time hours portion."""

    _attr_name = "Remaining Time Hours"
    _attr_icon = "mdi:clock-time-four-outline"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, coordinator, device, entry):
        """Initialize the remaining time hours sensor."""
        super().__init__(coordinator, device, entry)
        self._attr_unique_id = f"{device.serial_number}_remaining_time_hours"

    @property
    def native_value(self) -> int:
        """Return the hours portion of remaining time."""
        total_minutes = self.coordinator.data.get("remaining_time", 0)
        return total_minutes // 60


class CrockpotRemainingTimeMinutesSensor(CrockpotSensorBase):
    """Sensor for remaining cooking time minutes portion."""

    _attr_name = "Remaining Time Minutes"
    _attr_icon = "mdi:clock-outline"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator, device, entry):
        """Initialize the remaining time minutes sensor."""
        super().__init__(coordinator, device, entry)
        self._attr_unique_id = f"{device.serial_number}_remaining_time_minutes"

    @property
    def native_value(self) -> int:
        """Return the minutes portion of remaining time."""
        total_minutes = self.coordinator.data.get("remaining_time", 0)
        return total_minutes % 60


class CrockpotCookedTimeSensor(CrockpotSensorBase):
    """Sensor for time already cooked."""

    _attr_name = "Cooked Time"
    _attr_icon = "mdi:clock-check"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator, device, entry):
        """Initialize the cooked time sensor."""
        super().__init__(coordinator, device, entry)
        self._attr_unique_id = f"{device.serial_number}_cooked_time"

    @property
    def native_value(self) -> int:
        """Return the cooked time in minutes."""
        return self.coordinator.data.get("cooked_time", 0)
