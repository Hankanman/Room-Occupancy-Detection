"""Constants and types for the Area Occupancy Detection integration."""

from __future__ import annotations

from typing import Final
from datetime import timedelta
from homeassistant.const import Platform

DOMAIN: Final = "area_occupancy"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER]

# Device information
DEVICE_MANUFACTURER: Final = "Hankanman"
DEVICE_MODEL: Final = "Area Occupancy Detector"
DEVICE_SW_VERSION: Final = "2024.12.3"

# Configuration constants
CONF_NAME: Final = "name"
CONF_MOTION_SENSORS: Final = "motion_sensors"
CONF_MEDIA_DEVICES: Final = "media_devices"
CONF_APPLIANCES: Final = "appliances"
CONF_ILLUMINANCE_SENSORS: Final = "illuminance_sensors"
CONF_HUMIDITY_SENSORS: Final = "humidity_sensors"
CONF_TEMPERATURE_SENSORS: Final = "temperature_sensors"
CONF_DOOR_SENSORS: Final = "door_sensors"
CONF_WINDOW_SENSORS: Final = "window_sensors"
CONF_LIGHTS: Final = "lights"
CONF_THRESHOLD: Final = "threshold"
CONF_HISTORY_PERIOD: Final = "history_period"
CONF_DECAY_ENABLED: Final = "decay_enabled"
CONF_DECAY_WINDOW: Final = "decay_window"
CONF_HISTORICAL_ANALYSIS_ENABLED: Final = "historical_analysis_enabled"
CONF_DEVICE_STATES: Final = "device_states"
CONF_AREA_ID: Final = "area_id"
CONF_DECAY_MIN_DELAY: Final = "decay_min_delay"

# Configured Weights
CONF_WEIGHT_MOTION: Final = "weight_motion"
CONF_WEIGHT_MEDIA: Final = "weight_media"
CONF_WEIGHT_APPLIANCE: Final = "weight_appliance"
CONF_WEIGHT_DOOR: Final = "weight_door"
CONF_WEIGHT_WINDOW: Final = "weight_window"
CONF_WEIGHT_LIGHT: Final = "weight_light"
CONF_WEIGHT_ENVIRONMENTAL: Final = "weight_environmental"

# File paths and configuration
CONF_VERSION: Final = 4
STORAGE_VERSION: Final = 5
STORAGE_VERSION_MINOR: Final = 1
CACHE_DURATION: Final = timedelta(hours=6)

# Default values
DEFAULT_THRESHOLD: Final = 50.0
DEFAULT_HISTORY_PERIOD: Final = 7  # days
DEFAULT_DECAY_ENABLED: Final = True
DEFAULT_DECAY_WINDOW: Final = 600  # seconds (10 minutes)
DEFAULT_HISTORICAL_ANALYSIS_ENABLED: Final = True
DEFAULT_DECAY_MIN_DELAY: Final = 60  # 1 minute

# Default weights
DEFAULT_WEIGHT_MOTION: Final = 0.85
DEFAULT_WEIGHT_MEDIA: Final = 0.7
DEFAULT_WEIGHT_APPLIANCE: Final = 0.3
DEFAULT_WEIGHT_DOOR: Final = 0.3
DEFAULT_WEIGHT_WINDOW: Final = 0.2
DEFAULT_WEIGHT_LIGHT: Final = 0.2
DEFAULT_WEIGHT_ENVIRONMENTAL: Final = 0.1

# Entity naming
NAME_PROBABILITY_SENSOR: Final = "Occupancy Probability"
NAME_BINARY_SENSOR: Final = "Occupancy Status"
NAME_PRIORS_SENSOR: Final = "Prior Probability"
NAME_DECAY_SENSOR = "Decay Status"
NAME_THRESHOLD_NUMBER: Final = "Occupancy Threshold"

# Decay lambda such that at half of decay_window probability is 25% of original
DECAY_LAMBDA = 0.866433976

# Safety bounds
MIN_PROBABILITY: Final[float] = 0.01
MAX_PROBABILITY: Final[float] = 0.99

# Default prior probabilities
DEFAULT_PRIOR: Final[float] = 0.1713
DEFAULT_PROB_GIVEN_TRUE: Final[float] = 0.3
DEFAULT_PROB_GIVEN_FALSE: Final[float] = 0.02

# Helper constants
ROUNDING_PRECISION: Final = 2
