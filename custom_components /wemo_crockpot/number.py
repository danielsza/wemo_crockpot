"""Number platform for WeMo Crockpot."""
from __future__ import annotations

import logging

from pywemo.ouimeaux_device.crockpot import CrockPotMode

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WeMo Crockpot number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device = data["device"]

    async_add_entities([
        CrockpotTimerHoursNumber(coordinator, device, entry),
        CrockpotTimerMinutesNumber(coordinator, device, entry),
    ])


class CrockpotTimerBase(CoordinatorEntity, NumberEntity):
    """Base class for Crockpot timer number entities."""

    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True

    def __init__(self, coordinator, device, entry):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device = device
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.serial_number)},
            "name": "Crockpot",
            "manufacturer": "Belkin",
            "model": getattr(device, 'model_name', "Crockpot"),
            "serial_number": device.serial_number,
        }

    def _get_total_minutes(self) -> int:
        """Get total remaining time in minutes."""
        return self.coordinator.data.get("remaining_time", 0)

    async def _set_total_minutes(self, total_minutes: int) -> None:
        """Set the total cooking time in minutes."""
        # Get the current mode from the device
        mode_value = self.coordinator.data.get("mode", 0)

        try:
            # Convert to CrockPotMode enum
            current_mode = CrockPotMode(mode_value)
            _LOGGER.info("Setting timer to %d minutes (current mode: %s)",
                        total_minutes, current_mode.name)

            # Use the pywemo CrockPot API - update_settings(mode, time)
            await self.hass.async_add_executor_job(
                self._device.update_settings, current_mode, total_minutes
            )
            _LOGGER.info("Successfully set timer to %d minutes", total_minutes)

            # Request immediate update to reflect the change
            await self.coordinator.async_request_refresh()
        except ValueError as err:
            _LOGGER.error("Invalid mode value %d: %s", mode_value, err)
        except Exception as err:
            _LOGGER.error("Failed to set timer to %d minutes: %s", total_minutes, err)


class CrockpotTimerHoursNumber(CrockpotTimerBase):
    """Number entity for Crockpot cooking timer hours."""

    _attr_name = "Timer Hours"
    _attr_icon = "mdi:clock-time-four-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, coordinator, device, entry):
        """Initialize the hours number entity."""
        super().__init__(coordinator, device, entry)
        self._attr_unique_id = f"{device.serial_number}_timer_hours"

    @property
    def native_value(self) -> float | None:
        """Return the hours portion of the timer."""
        total_minutes = self._get_total_minutes()
        hours = total_minutes // 60
        _LOGGER.debug("Current timer hours: %d (from %d total minutes)", hours, total_minutes)
        return float(hours)

    async def async_set_native_value(self, value: float) -> None:
        """Set the hours portion of the timer."""
        new_hours = int(value)

        # Get current minutes portion (remainder after removing hours)
        total_minutes = self._get_total_minutes()
        current_minutes_portion = total_minutes % 60

        # Calculate new total
        new_total_minutes = (new_hours * 60) + current_minutes_portion

        _LOGGER.info("Setting timer hours to %d (minutes portion: %d, total: %d)",
                    new_hours, current_minutes_portion, new_total_minutes)

        await self._set_total_minutes(new_total_minutes)


class CrockpotTimerMinutesNumber(CrockpotTimerBase):
    """Number entity for Crockpot cooking timer minutes."""

    _attr_name = "Timer Minutes"
    _attr_icon = "mdi:clock-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = 59
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator, device, entry):
        """Initialize the minutes number entity."""
        super().__init__(coordinator, device, entry)
        self._attr_unique_id = f"{device.serial_number}_timer_minutes"

    @property
    def native_value(self) -> float | None:
        """Return the minutes portion of the timer."""
        total_minutes = self._get_total_minutes()
        minutes = total_minutes % 60
        _LOGGER.debug("Current timer minutes: %d (from %d total minutes)", minutes, total_minutes)
        return float(minutes)

    async def async_set_native_value(self, value: float) -> None:
        """Set the minutes portion of the timer."""
        new_minutes = int(value)

        # Get current hours portion
        total_minutes = self._get_total_minutes()
        current_hours = total_minutes // 60

        # Calculate new total
        new_total_minutes = (current_hours * 60) + new_minutes

        _LOGGER.info("Setting timer minutes to %d (hours portion: %d, total: %d)",
                    new_minutes, current_hours, new_total_minutes)

        await self._set_total_minutes(new_total_minutes)
