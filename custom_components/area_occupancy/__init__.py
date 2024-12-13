"""The Area Occupancy Detection integration."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    STORAGE_KEY_HISTORY,
    STORAGE_VERSION,
    CONF_AREA_ID,
    CONF_MOTION_SENSORS,
    CONF_THRESHOLD,
    CONF_HISTORY_PERIOD,
    CONF_DECAY_WINDOW,
    CONF_MINIMUM_CONFIDENCE,
)
from .types import StorageData, CoreConfig, OptionsConfig
from .coordinator import AreaOccupancyCoordinator
from .service import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


def validate_core_config(data: dict[str, Any]) -> CoreConfig:
    """Validate core configuration data."""
    if not data.get(CONF_NAME):
        raise HomeAssistantError("Name is required")

    if not data.get(CONF_MOTION_SENSORS):
        raise HomeAssistantError("At least one motion sensor is required")

    if not data.get(CONF_AREA_ID):
        raise HomeAssistantError("Area ID is required")

    return CoreConfig(
        name=data[CONF_NAME],
        area_id=data[CONF_AREA_ID],
        motion_sensors=data[CONF_MOTION_SENSORS],
    )


def validate_numeric_bounds(data: dict[str, Any]) -> None:
    """Validate numeric values are within acceptable bounds."""
    if CONF_THRESHOLD in data and not 0 <= data[CONF_THRESHOLD] <= 1:
        raise HomeAssistantError("Threshold must be between 0 and 1")

    if CONF_HISTORY_PERIOD in data and not 1 <= data[CONF_HISTORY_PERIOD] <= 30:
        raise HomeAssistantError("History period must be between 1 and 30 days")

    if CONF_DECAY_WINDOW in data and not 60 <= data[CONF_DECAY_WINDOW] <= 3600:
        raise HomeAssistantError("Decay window must be between 60 and 3600 seconds")

    if CONF_MINIMUM_CONFIDENCE in data and not 0 <= data[CONF_MINIMUM_CONFIDENCE] <= 1:
        raise HomeAssistantError("Minimum confidence must be between 0 and 1")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Area Occupancy Detection integration."""
    hass.data.setdefault(DOMAIN, {})

    # Set up services
    await async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Area Occupancy Detection from a config entry."""
    try:
        # Initialize domain data if not exists
        hass.data.setdefault(DOMAIN, {})

        # Validate core configuration
        try:
            core_config = validate_core_config(entry.data)
            _LOGGER.debug("Core config validated: %s", core_config)
        except Exception as err:
            _LOGGER.error("Core config validation failed: %s", err)
            raise HomeAssistantError(f"Core config validation failed: {err}") from err

        # Validate options configuration
        try:
            options_config = dict(entry.options)
            validate_numeric_bounds(options_config)
            _LOGGER.debug("Options config validated: %s", options_config)
        except Exception as err:
            _LOGGER.error("Options config validation failed: %s", err)
            raise HomeAssistantError(
                f"Options config validation failed: {err}"
            ) from err

        # Initialize storage with unique key per entry
        store = Store[StorageData](
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_HISTORY}_{entry.entry_id}",
            atomic_writes=True,
        )

        # Load historical data and pass it to coordinator
        stored_data = await store.async_load() or {
            "version": STORAGE_VERSION,
            "last_updated": "",
            "areas": {},
        }

        # Initialize coordinator with stored data
        coordinator = AreaOccupancyCoordinator(
            hass=hass,
            entry_id=entry.entry_id,
            core_config=core_config,
            options_config=options_config,
            store=store,
            stored_data=stored_data,  # Pass stored data to coordinator
        )

        # Setup coordinator
        try:
            await coordinator.async_setup()
        except Exception as err:
            raise ConfigEntryNotReady(f"Failed to setup coordinator: {err}") from err

        # Perform first update
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception as err:
            raise ConfigEntryNotReady(
                f"Failed to perform initial data refresh: {err}"
            ) from err

        # Store components
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "store": store,
        }

        # Set up entry update listener
        entry.async_on_unload(entry.add_update_listener(async_update_options))

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.debug(
            "Successfully set up Area Occupancy for %s with ID %s",
            core_config["name"],
            entry.entry_id,
        )

        return True

    except ConfigEntryNotReady as ready_err:
        raise ready_err

    except Exception as err:
        _LOGGER.error("Failed to set up Area Occupancy integration: %s", err)
        raise ConfigEntryNotReady(
            f"Failed to set up Area Occupancy integration: {err}"
        ) from err


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        # Unload platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            coordinator: AreaOccupancyCoordinator = hass.data[DOMAIN][entry.entry_id][
                "coordinator"
            ]
            store: Store = hass.data[DOMAIN][entry.entry_id]["store"]

            # Clean up coordinator and save final state
            coordinator.unsubscribe()
            await store.async_save(coordinator.get_storage_data())

            # Remove entry data
            hass.data[DOMAIN].pop(entry.entry_id)

            # If this is the last config entry, remove services
            if not hass.config_entries.async_entries(DOMAIN):
                await async_unload_services(hass)

            _LOGGER.debug(
                "Successfully unloaded Area Occupancy entry %s", entry.entry_id
            )

        return unload_ok

    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error unloading entry: %s", err)
        return False


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options for existing area occupancy entry."""
    try:
        # Validate new options
        new_options = dict(entry.options)
        validate_numeric_bounds(new_options)

        # Get coordinator
        coordinator: AreaOccupancyCoordinator = hass.data[DOMAIN][entry.entry_id][
            "coordinator"
        ]

        # Update coordinator with validated options
        coordinator.update_options(new_options)

        # Reload entry
        await hass.config_entries.async_reload(entry.entry_id)

        _LOGGER.debug(
            "Successfully updated options for Area Occupancy entry %s",
            entry.entry_id,
        )

    except Exception as err:
        _LOGGER.error("Error updating options: %s", err)
        raise HomeAssistantError(f"Failed to update options: {err}") from err


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry to new version."""
    _LOGGER.debug(
        "Migrating Area Occupancy entry from version %s", config_entry.version
    )

    try:
        if config_entry.version == 1:
            # Migrate to version 2
            core_config, options_config = migrate_legacy_config(config_entry.data)

            # Add area_id if not present
            if CONF_AREA_ID not in core_config:
                core_config[CONF_AREA_ID] = str(uuid.uuid4())

            # Update config entry with new format
            hass.config_entries.async_update_entry(
                config_entry,
                data=core_config,
                options=options_config,
                version=2,
                unique_id=core_config[CONF_AREA_ID],
            )

            _LOGGER.info(
                "Successfully migrated Area Occupancy entry %s to version 2",
                config_entry.entry_id,
            )
            return True

        return False

    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error migrating Area Occupancy configuration: %s", err)
        return False


def migrate_legacy_config(config: dict[str, Any]) -> tuple[CoreConfig, OptionsConfig]:
    """Migrate legacy configuration to new format."""
    try:
        core_config = CoreConfig(
            name=config[CONF_NAME],
            area_id=config.get(CONF_AREA_ID),
            motion_sensors=config[CONF_MOTION_SENSORS],
        )

        options_data = {
            k: v
            for k, v in config.items()
            if k not in [CONF_NAME, CONF_MOTION_SENSORS, CONF_AREA_ID]
        }
        validate_numeric_bounds(options_data)

        return core_config, options_data

    except Exception as err:
        _LOGGER.error("Error migrating config: %s", err)
        raise HomeAssistantError(f"Failed to migrate configuration: {err}") from err
