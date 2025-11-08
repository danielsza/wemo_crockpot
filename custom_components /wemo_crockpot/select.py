"""Select platform for WeMo Crockpot."""
from __future__ import annotations

import logging

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
        # Get state from coordinator data
        state = self.coordinator.data.get("state")
        if state is None:
            _LOGGER.debug("No state data available")
            return None

        # Convert state number to mode string
        state_str = str(state)
        mode = MODES.get(state_str, "Off")
        _LOGGER.debug("Current state: %s (raw: %s) -> mode: %s", state_str, state, mode)

        # Use mode_string from device if available as fallback
        if mode == "Off" and state_str != "0":
            mode_string = self.coordinator.data.get("mode_string")
            if mode_string:
                _LOGGER.warning("State %s not found in MODES, using mode_string: %s", state_str, mode_string)
                return mode_string

        return mode

    async def async_select_option(self, option: str) -> None:
        """Change the cooking mode."""
        # Get the numeric value for this mode
        mode_value = MODE_TO_VALUE.get(option)
        
        if mode_value is None:
            _LOGGER.error("Invalid mode: %s", option)
            return

        _LOGGER.info("Setting crockpot mode to %s (value: %s)", option, mode_value)

        try:
            # Set the state using the numeric mode value
            await self.hass.async_add_executor_job(
                self._device.set_state, int(mode_value)
            )
            # Request immediate update
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set mode to %s: %s", option, err)
