"""Coordinator for Room Occupancy Detection."""

from __future__ import annotations

import logging
import math
from datetime import timedelta
from typing import Any

from homeassistant.const import (
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DECAY_ENABLED,
    CONF_DECAY_TYPE,
    CONF_DECAY_WINDOW,
    CONF_DEVICE_STATES,
    CONF_HUMIDITY_SENSORS,
    CONF_ILLUMINANCE_SENSORS,
    CONF_MOTION_SENSORS,
    CONF_TEMPERATURE_SENSORS,
    DEFAULT_DECAY_ENABLED,
    DEFAULT_DECAY_TYPE,
    DEFAULT_DECAY_WINDOW,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class RoomOccupancyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching room occupancy data."""

    def __init__(
        self, hass: HomeAssistant, entry_id: str, config: dict[str, Any]
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.entry_id = entry_id
        self.config = config
        self._motion_timestamps = {}
        self._sensor_states = {}
        self._unsubscribe_handlers = []
        self._initialize_sensor_states()
        self._setup_state_listeners()

    def _initialize_sensor_states(self) -> None:
        """Initialize states for all configured sensors."""
        sensors = self._get_all_configured_sensors()
        for entity_id in sensors:
            state = self.hass.states.get(entity_id)
            if state:
                self._sensor_states[entity_id] = state

    def _get_all_configured_sensors(self) -> list[str]:
        """Get list of all configured sensor entity IDs."""
        sensors = []
        sensors.extend(self.config.get(CONF_MOTION_SENSORS, []))
        sensors.extend(self.config.get(CONF_ILLUMINANCE_SENSORS, []))
        sensors.extend(self.config.get(CONF_HUMIDITY_SENSORS, []))
        sensors.extend(self.config.get(CONF_TEMPERATURE_SENSORS, []))
        sensors.extend(self.config.get(CONF_DEVICE_STATES, []))
        return sensors

    def unsubscribe(self) -> None:
        """Unsubscribe from all registered events."""
        while self._unsubscribe_handlers:
            self._unsubscribe_handlers.pop()()

    def _setup_state_listeners(self) -> None:
        """Set up state change listeners for all configured sensors."""
        sensors = self._get_all_configured_sensors()

        @callback
        def async_state_changed(event):
            """Handle sensor state changes."""
            entity_id = event.data["entity_id"]
            new_state = event.data["new_state"]
            old_state = event.data["old_state"]

            # Only update if state actually changed
            if new_state != old_state:
                self._sensor_states[entity_id] = new_state
                if (
                    entity_id in self.config.get(CONF_MOTION_SENSORS, [])
                    and new_state
                    and new_state.state == STATE_ON
                ):
                    self._motion_timestamps[entity_id] = dt_util.utcnow()
                self.async_set_updated_data(None)

        self.unsubscribe()
        self._unsubscribe_handlers.append(
            async_track_state_change_event(self.hass, sensors, async_state_changed)
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from sensors and calculate occupancy probability."""
        # Refresh all sensor states to ensure we have current data
        self._refresh_sensor_states()

        motion_prob = self._calculate_motion_probability()
        env_prob = self._calculate_environmental_probability()
        combined_prob = (motion_prob.probability * 0.7) + (env_prob.probability * 0.3)

        active_sensors = len(
            [
                sensor
                for sensor, available in self._get_sensor_availability().items()
                if available
            ]
        )
        total_sensors = len(self._get_all_configured_sensors())

        return {
            "probability": combined_prob,
            "prior_probability": motion_prob.probability,
            "active_triggers": motion_prob.triggers + env_prob.triggers,
            "sensor_probabilities": {
                "motion_probability": motion_prob.probability,
                "environmental_probability": env_prob.probability,
            },
            "decay_status": self._get_decay_status(),
            "confidence_score": self._calculate_confidence_score(
                active_sensors, total_sensors
            ),
            "sensor_availability": self._get_sensor_availability(),
        }

    def _refresh_sensor_states(self) -> None:
        """Refresh all sensor states from Home Assistant."""
        for entity_id in self._get_all_configured_sensors():
            state = self.hass.states.get(entity_id)
            if state:
                self._sensor_states[entity_id] = state

    class ProbabilityResult:
        """Class to hold probability calculation results."""

        def __init__(self, probability: float, triggers: list[str]) -> None:
            """Initialize probability result."""
            self.probability = probability
            self.triggers = triggers

    def _calculate_motion_probability(self) -> ProbabilityResult:
        """Calculate probability based on motion sensors."""
        active_triggers = []
        now = dt_util.utcnow()
        decay_window = self.config.get(CONF_DECAY_WINDOW, DEFAULT_DECAY_WINDOW)
        decay_enabled = self.config.get(CONF_DECAY_ENABLED, DEFAULT_DECAY_ENABLED)
        decay_type = self.config.get(CONF_DECAY_TYPE, DEFAULT_DECAY_TYPE)

        motion_probability = 0.0
        total_weight = len(self.config.get(CONF_MOTION_SENSORS, []))

        if total_weight == 0:
            return self.ProbabilityResult(0.0, [])

        for entity_id in self.config.get(CONF_MOTION_SENSORS, []):
            state = self._sensor_states.get(entity_id)
            if not state or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                total_weight -= 1
                continue

            if state.state == STATE_ON:
                motion_probability += 1.0
                active_triggers.append(entity_id)
            elif decay_enabled and entity_id in self._motion_timestamps:
                last_motion = self._motion_timestamps[entity_id]
                time_diff = (now - last_motion).total_seconds()

                if time_diff < decay_window:
                    decay_factor = 1.0
                    if decay_type == "linear":
                        decay_factor = 1.0 - (time_diff / decay_window)
                    else:  # exponential
                        decay_factor = math.exp(-3.0 * time_diff / decay_window)

                    motion_probability += decay_factor
                    if decay_factor > 0.1:
                        active_triggers.append(
                            f"{entity_id} (decay: {decay_factor:.2f})"
                        )

        final_probability = (
            motion_probability / total_weight if total_weight > 0 else 0.0
        )
        return self.ProbabilityResult(final_probability, active_triggers)

    def _calculate_environmental_probability(self) -> ProbabilityResult:
        """Calculate probability based on environmental sensors."""
        active_triggers = []
        total_probability = 0.0
        total_sensors = 0

        # Process illuminance sensors
        for entity_id in self.config.get(CONF_ILLUMINANCE_SENSORS, []):
            state = self._sensor_states.get(entity_id)
            if not state or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                continue

            try:
                current_value = float(state.state)
                if current_value > 50:
                    total_probability += 0.7
                    active_triggers.append(f"{entity_id} ({current_value} lx)")
                total_sensors += 1
            except ValueError:
                continue

        # Process temperature and humidity sensors
        for sensor_type, threshold, unit in [
            (CONF_TEMPERATURE_SENSORS, 1.5, "°C"),
            (CONF_HUMIDITY_SENSORS, 10, "%"),
        ]:
            changes = []
            for entity_id in self.config.get(sensor_type, []):
                state = self._sensor_states.get(entity_id)
                if not state or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                    continue

                try:
                    current_value = float(state.state)
                    baseline = 21 if sensor_type == CONF_TEMPERATURE_SENSORS else 50
                    if abs(current_value - baseline) > threshold:
                        changes.append(current_value)
                        active_triggers.append(f"{entity_id} ({current_value}{unit})")
                    total_sensors += 1
                except ValueError:
                    continue

            if changes:
                total_probability += (
                    0.5 if sensor_type == CONF_HUMIDITY_SENSORS else 0.6
                )

        # Process device states
        for entity_id in self.config.get(CONF_DEVICE_STATES, []):
            state = self._sensor_states.get(entity_id)
            if not state or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                continue

            if state.state == STATE_ON:
                total_probability += 0.8
                active_triggers.append(entity_id)
                total_sensors += 1

        final_probability = (
            total_probability / total_sensors if total_sensors > 0 else 0.0
        )
        return self.ProbabilityResult(final_probability, active_triggers)

    def _calculate_confidence_score(
        self, active_sensors: int, total_sensors: int
    ) -> float:
        """Calculate confidence score based on sensor availability."""
        if total_sensors == 0:
            return 0.0
        return min(active_sensors / total_sensors, 1.0)

    def _get_sensor_availability(self) -> dict[str, bool]:
        """Get availability status of all sensors."""
        availability = {}
        for sensor_type in [
            CONF_MOTION_SENSORS,
            CONF_ILLUMINANCE_SENSORS,
            CONF_HUMIDITY_SENSORS,
            CONF_TEMPERATURE_SENSORS,
            CONF_DEVICE_STATES,
        ]:
            for entity_id in self.config.get(sensor_type, []):
                state = self._sensor_states.get(entity_id)
                availability[entity_id] = state is not None and state.state not in (
                    STATE_UNAVAILABLE,
                    STATE_UNKNOWN,
                )
        return availability

    def _get_decay_status(self) -> dict[str, float]:
        """Get decay status for motion sensors."""
        decay_status = {}
        if self.config.get(CONF_DECAY_ENABLED, DEFAULT_DECAY_ENABLED):
            now = dt_util.utcnow()
            decay_window = self.config.get(CONF_DECAY_WINDOW, DEFAULT_DECAY_WINDOW)
            for entity_id, last_motion in self._motion_timestamps.items():
                time_diff = (now - last_motion).total_seconds()
                if time_diff < decay_window:
                    decay_status[entity_id] = time_diff
        return decay_status
