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

    async_add_entities([CrockpotTimerNumber(coordinator, device, entry)])


class CrockpotTimerNumber(CoordinatorEntity, NumberEntity):
    """Number entity for Crockpot cooking timer."""

    _attr_name = "Timer"
    _attr_icon = "mdi:timer"
    _attr_native_min_value = 0
    _attr_native_max_value = 1440  # 24 hours in minutes
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True

    def __init__(self, coordinator, device, entry):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device = device
        self._entry = entry
        self._attr_unique_id = f"{device.serial_number}_timer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.serial_number)},
            "name": "Crockpot",
            "manufacturer": "Belkin",
            "model": getattr(device, 'model_name', "Crockpot"),
            "serial_number": device.serial_number,
        }

    @property
    def native_value(self) -> float | None:
        """Return the current timer value in minutes."""
        # Get remaining time from coordinator
        remaining = self.coordinator.data.get("remaining_time")
        if remaining is not None:
            _LOGGER.debug("Current timer value: %d minutes", remaining)
            return float(remaining)
        return 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the cooking timer."""
        time_minutes = int(value)

        # Get the current mode from the device
        mode_value = self.coordinator.data.get("mode", 0)

        try:
            # Convert to CrockPotMode enum
            current_mode = CrockPotMode(mode_value)
            _LOGGER.info("Setting timer to %d minutes (current mode: %s)",
                        time_minutes, current_mode.name)

            # Use the pywemo CrockPot API - update_settings(mode, time)
            await self.hass.async_add_executor_job(
                self._device.update_settings, current_mode, time_minutes
            )
            _LOGGER.info("Successfully set timer to %d minutes", time_minutes)

            # Request immediate update to reflect the change
            await self.coordinator.async_request_refresh()
        except ValueError as err:
            _LOGGER.error("Invalid mode value %d: %s", mode_value, err)
        except Exception as err:
            _LOGGER.error("Failed to set timer to %d minutes: %s", time_minutes, err)
