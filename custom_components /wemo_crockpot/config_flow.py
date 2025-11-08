"""Config flow for WeMo Crockpot integration."""
from __future__ import annotations

import logging
from typing import Any

import pywemo
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WeMoCrockpotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WeMo Crockpot."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            
            # Try to connect to the device
            try:
                _LOGGER.info("Probing WeMo device at %s", host)
                port = await self.hass.async_add_executor_job(
                    pywemo.ouimeaux_device.probe_wemo, host
                )
                
                _LOGGER.info("Probe result for %s: port=%s", host, port)
                
                if not port:
                    _LOGGER.error("Failed to probe WeMo device at %s", host)
                    errors["base"] = "cannot_connect"
                else:
                    url = f"http://{host}:{port}/setup.xml"
                    _LOGGER.info("Attempting to get device description from %s", url)
                    
                    device = await self.hass.async_add_executor_job(
                        pywemo.discovery.device_from_description, url
                    )
                    
                    _LOGGER.info("Device type: %s, Device: %s", type(device).__name__, device)
                    
                    if device is None:
                        _LOGGER.error("device_from_description returned None for %s", url)
                        errors["base"] = "cannot_connect"
                    else:
                        # For now, accept any WeMo device
                        # We'll check if it's a crockpot but won't reject it
                        is_crockpot = False
                        
                        # Method 1: Check if pywemo recognized it as a CrockPot
                        if isinstance(device, pywemo.CrockPot):
                            is_crockpot = True
                            _LOGGER.info("Device recognized as CrockPot by pywemo")
                        
                        # Method 2: Check model name (fallback)
                        elif hasattr(device, 'model_name') and device.model_name:
                            model_lower = device.model_name.lower()
                            if 'crockpot' in model_lower or 'crock' in model_lower:
                                is_crockpot = True
                                _LOGGER.info("Device identified as CrockPot by model name: %s", device.model_name)
                        
                        # Method 3: Check device type from basic info (fallback)
                        elif hasattr(device, 'device_type') and device.device_type:
                            if 'crockpot' in device.device_type.lower():
                                is_crockpot = True
                                _LOGGER.info("Device identified as CrockPot by device_type: %s", device.device_type)
                        
                        if not is_crockpot:
                            _LOGGER.warning(
                                "Device at %s does not appear to be a CrockPot. "
                                "Type: %s, Model: %s, DeviceType: %s - Proceeding anyway for testing",
                                host,
                                type(device).__name__,
                                getattr(device, 'model_name', 'unknown'),
                                getattr(device, 'device_type', 'unknown')
                            )
                        
                        # Create entry regardless
                        _LOGGER.info("Creating config entry for device: %s", device.name)
                        await self.async_set_unique_id(device.serial_number)
                        self._abort_if_unique_id_configured()
                        
                        return self.async_create_entry(
                            title=f"WeMo Crockpot ({host})",
                            data={CONF_HOST: host},
                        )
                        
            except Exception as err:
                _LOGGER.exception("Unexpected exception connecting to %s: %s", host, err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )
