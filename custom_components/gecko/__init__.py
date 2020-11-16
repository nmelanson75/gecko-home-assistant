"""
Custom integration to integrate Gecko with Home Assistant.

For more details about this integration, please refer to
https://github.com/gazoodle/gecko-home-assistant
"""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant

from geckolib import GeckoLocator

from .const import (
    CONF_SPA_IDENTIFIER,
    GECKOLIB_MANAGER_UUID,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    spa_identifier = entry.data.get(CONF_SPA_IDENTIFIER)

    with GeckoLocator(GECKOLIB_MANAGER_UUID) as locator:
        datablock = GeckoDataBlock(
            locator.get_spa_from_identifier(spa_identifier).get_facade(), entry
        )

        hass.data[DOMAIN][entry.entry_id] = datablock

        for platform in datablock.platforms:
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

        entry.add_update_listener(async_reload_entry)
    return True


class GeckoDataBlock:
    def __init__(self, facade, entry: ConfigEntry):
        self.facade = facade
        self.platforms = [
            platform for platform in PLATFORMS if entry.options.get(platform, True)
        ]


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    datablock = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in datablock.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    _LOGGER.info("async_reload_entry called")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)