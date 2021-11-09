"""The Vconnex integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .vconnex_wrap import init_sdk, release_sdk

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Async setup hass config entry."""
    hass.data.setdefault(DOMAIN, {})
    vconnex_data = await init_sdk(hass, entry)
    if vconnex_data is None:
        return False

    hass.data[DOMAIN][entry.entry_id] = vconnex_data
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        vconnex_data = hass.data[DOMAIN].pop(entry.entry_id)
        release_sdk(vconnex_data)

    return unload_ok
