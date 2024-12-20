"""The Area Occupancy Detection integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_VERSION,
)
from .coordinator import AreaOccupancyCoordinator
from .service import async_setup_services
from .helpers import async_migrate_entry

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Area Occupancy Detection integration."""
    _LOGGER.debug("Starting async_setup")
    hass.data.setdefault(DOMAIN, {})

    # Set up services
    await async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Area Occupancy Detection from a config entry."""
    _LOGGER.debug("Starting async_setup_entry for %s", entry.entry_id)
    try:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.debug("Checking entry version")

        # Check if area_id is present and needs migration
        if entry.version < CONF_VERSION or not entry.version:
            _LOGGER.debug(
                "Migrating entry from version %s to %s", entry.version, CONF_VERSION
            )
            if not await async_migrate_entry(hass, entry):
                _LOGGER.error("Migration failed for entry %s", entry.entry_id)
                return False

        _LOGGER.debug("Creating coordinator for entry %s", entry.entry_id)
        # Initialize the coordinator with the unified configuration
        coordinator = AreaOccupancyCoordinator(hass, entry)

        _LOGGER.debug("Loading stored data")
        # Load stored data and initialize states
        await coordinator.async_load_stored_data()

        _LOGGER.debug("Initializing states")
        await coordinator.async_initialize_states()

        _LOGGER.debug("Performing initial refresh")
        # Trigger an initial refresh
        await coordinator.async_refresh()

        _LOGGER.debug("Storing coordinator")
        # Store the coordinator for future use
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

        _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Add an update listener to handle configuration updates
        entry.async_on_unload(entry.add_update_listener(async_update_options))

        _LOGGER.debug("Setup complete for entry %s", entry.entry_id)
        return True

    except Exception as err:
        _LOGGER.exception(
            "Failed to set up Area Occupancy integration for entry %s: %s",
            entry.entry_id,
            err,
        )
        raise ConfigEntryNotReady(str(err)) from err


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when configuration is changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options when config entry is updated."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_update_options()
