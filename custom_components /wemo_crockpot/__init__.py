"""WeMo Crockpot Integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

import pywemo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

DOMAIN = "wemo_crockpot"
PLATFORMS = [Platform.SENSOR, Platform.SELECT]

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WeMo Crockpot from a config entry."""
    host = entry.data[CONF_HOST]
    
    # Discover and connect to the Crockpot
    try:
        url = await hass.async_add_executor_job(_discover_crockpot, host)
        if not url:
            _LOGGER.error("Could not discover WeMo Crockpot at %s", host)
            return False
            
        device = await hass.async_add_executor_job(pywemo.discovery.device_from_description, url)
        
        _LOGGER.info("Connected to device: %s (Type: %s, Model: %s)", 
                     device.name, type(device).__name__, 
                     getattr(device, 'model_name', 'unknown'))
            
    except Exception as err:
        _LOGGER.error("Failed to connect to WeMo Crockpot: %s", err)
        return False

    # Create update coordinator
    async def async_update_data():
        """Fetch data from the Crockpot."""
        try:
            # Get the current state - for crockpot this is the mode
            state = await hass.async_add_executor_job(device.get_state, True)
            
            # Try to get additional attributes if they exist
            data = {"state": state}
            
            # Check for crockpot-specific attributes
            if hasattr(device, 'mode'):
                data["mode"] = device.mode
            if hasattr(device, 'mode_string'):
                data["mode_string"] = device.mode_string
            if hasattr(device, 'remaining_time'):
                data["remaining_time"] = device.remaining_time
            if hasattr(device, 'cooked_time'):
                data["cooked_time"] = device.cooked_time
                
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"WeMo Crockpot {host}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and device
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device": device,
    }

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def _discover_crockpot(host: str) -> str | None:
    """Discover WeMo Crockpot on the network."""
    try:
        # Try to discover by host
        port = pywemo.ouimeaux_device.probe_wemo(host)
        if port:
            return f"http://{host}:{port}/setup.xml"
    except Exception as err:
        _LOGGER.debug("Error discovering device at %s: %s", host, err)
    
    return None
