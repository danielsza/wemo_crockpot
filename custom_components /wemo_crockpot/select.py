"""Select platform for WeMo Crockpot."""
from __future__ import annotations

import logging

from pywemo.ouimeaux_device.crockpot import CrockPotMode

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODES, MODE_TO_VALUE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WeMo Crockpot select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device = data["device"]

    async_add_entities([CrockpotModeSelect(coordinator, device, entry)])


class CrockpotModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity for Crockpot cooking mode."""

    _attr_name = "Mode"
    _attr_icon = "mdi:pot-steam"
    _attr_has_entity_name = True

    def __init__(self, coordinator, device, entry):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._device = device
        self._entry = entry
        self._attr_unique_id = f"{device.serial_number}_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.serial_number)},
            "name": f"Crockpot",
            "manufacturer": "Belkin",
            "model": getattr(device, 'model_name', "Crockpot"),
            "serial_number": device.serial_number,
        }
        self._attr_options = list(MODES.values())

    @property
    def current_option(self) -> str | None:
        """Return the current mode."""
        # Try to get mode directly from device (pywemo CrockPot has a mode attribute)
        mode_value = self.coordinator.data.get("mode")

        if mode_value is not None:
            # mode is already a CrockPotMode enum value
            mode_name = MODES.get(mode_value)
            if mode_name:
                _LOGGER.debug("Current mode from device.mode: %s (%d)", mode_name, mode_value)
                return mode_name

        # Fallback: use mode_string if available
        mode_string = self.coordinator.data.get("mode_string")
        if mode_string:
            _LOGGER.debug("Using mode_string: %s", mode_string)
            # Map mode_string to our standard names
            if mode_string in ["Turned Off", "Off"]:
                return "Off"
            return mode_string

        _LOGGER.warning("No mode data available from coordinator")
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the cooking mode."""
        # Get the numeric value for this mode
        mode_value = MODE_TO_VALUE.get(option)

        if mode_value is None:
            _LOGGER.error("Invalid mode: %s", option)
            return

        try:
            # Convert to CrockPotMode enum
            crockpot_mode = CrockPotMode(mode_value)
            _LOGGER.info("Setting crockpot mode to '%s' (CrockPotMode: %s, value: %d)",
                         option, crockpot_mode.name, mode_value)

            # Use the pywemo CrockPot API - update_settings(mode, time)
            # Keep the current cooking time (0 means no change to time)
            await self.hass.async_add_executor_job(
                self._device.update_settings, crockpot_mode, 0
            )
            _LOGGER.info("Successfully set mode to %s", crockpot_mode.name)

            # Request immediate update to reflect the change
            await self.coordinator.async_request_refresh()
        except ValueError as err:
            _LOGGER.error("Invalid CrockPotMode value %d for option %s: %s", mode_value, option, err)
        except Exception as err:
            _LOGGER.error("Failed to set mode to %s: %s", option, err)
