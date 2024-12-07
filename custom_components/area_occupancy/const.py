"""Constants and types for the Area Occupancy Detection integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "area_occupancy"

# Configuration constants
CONF_MOTION_SENSORS: Final = "motion_sensors"
CONF_MEDIA_DEVICES: Final = "media_devices"
CONF_APPLIANCES: Final = "appliances"
CONF_ILLUMINANCE_SENSORS: Final = "illuminance_sensors"
CONF_HUMIDITY_SENSORS: Final = "humidity_sensors"
CONF_TEMPERATURE_SENSORS: Final = "temperature_sensors"
CONF_THRESHOLD: Final = "threshold"
CONF_HISTORY_PERIOD: Final = "history_period"
CONF_DECAY_ENABLED: Final = "decay_enabled"
CONF_DECAY_WINDOW: Final = "decay_window"
CONF_DECAY_TYPE: Final = "decay_type"
CONF_HISTORICAL_ANALYSIS_ENABLED: Final = "historical_analysis_enabled"
CONF_MINIMUM_CONFIDENCE: Final = "minimum_confidence"
CONF_DEVICE_STATES: Final = "device_states"
CONF_AREA_ID: Final = "area_id"

# File paths and configuration
STORAGE_KEY_HISTORY: Final = "area_occupancy_history"
STORAGE_KEY_PATTERNS: Final = "area_occupancy_patterns"
STORAGE_VERSION: Final = 1

# Default values
DEFAULT_THRESHOLD: Final = 0.5
DEFAULT_HISTORY_PERIOD: Final = 7  # days
DEFAULT_DECAY_ENABLED: Final = True
DEFAULT_DECAY_WINDOW: Final = 600  # seconds (10 minutes)
DEFAULT_DECAY_TYPE: Final = "linear"
DEFAULT_HISTORICAL_ANALYSIS_ENABLED: Final = True
DEFAULT_MINIMUM_CONFIDENCE: Final = 0.3

# Entity naming
NAME_PROBABILITY_SENSOR: Final = "Occupancy Probability"
NAME_BINARY_SENSOR: Final = "Occupancy Status"
NAME_MOTION_PRIOR_SENSOR: Final = "Motion Prior"
NAME_ENVIRONMENTAL_PRIOR_SENSOR: Final = "Environmental Prior"
NAME_MEDIA_PRIOR_SENSOR: Final = "Media Prior"
NAME_APPLIANCE_PRIOR_SENSOR: Final = "Appliance Prior"
NAME_OCCUPANCY_PRIOR_SENSOR: Final = "Occupancy Prior"

# Attribute keys
ATTR_PROBABILITY: Final = "probability"
ATTR_PRIOR_PROBABILITY: Final = "prior_probability"
ATTR_ACTIVE_TRIGGERS: Final = "active_triggers"
ATTR_SENSOR_PROBABILITIES: Final = "sensor_probabilities"
ATTR_DECAY_STATUS: Final = "decay_status"
ATTR_CONFIDENCE_SCORE: Final = "confidence_score"
ATTR_SENSOR_AVAILABILITY: Final = "sensor_availability"
ATTR_LAST_OCCUPIED: Final = "last_occupied"
ATTR_STATE_DURATION: Final = "state_duration"
ATTR_OCCUPANCY_RATE: Final = "occupancy_rate"
ATTR_MOVING_AVERAGE: Final = "moving_average"
ATTR_RATE_OF_CHANGE: Final = "rate_of_change"
ATTR_MIN_PROBABILITY: Final = "min_probability"
ATTR_MAX_PROBABILITY: Final = "max_probability"
ATTR_THRESHOLD: Final = "threshold"
ATTR_WINDOW_SIZE: Final = "window_size"
ATTR_MEDIA_STATES: Final = "media_states"
ATTR_APPLIANCE_STATES: Final = "appliance_states"
ATTR_HISTORICAL_PATTERNS: Final = "historical_patterns"
ATTR_TYPICAL_OCCUPANCY: Final = "typical_occupancy_rate"
ATTR_DAY_OCCUPANCY: Final = "day_occupancy_rate"
ATTR_SENSOR_CORRELATIONS: Final = "sensor_correlations"

# Prior probability attributes
ATTR_TOTAL_SAMPLES: Final = "total_samples"
ATTR_ACTIVE_SAMPLES: Final = "active_samples"
ATTR_SAMPLING_PERIOD: Final = "sampling_period"
ATTR_MOTION_PRIOR: Final = "motion_prior"
ATTR_ENVIRONMENTAL_PRIOR: Final = "environmental_prior"
ATTR_MEDIA_PRIOR: Final = "media_prior"
ATTR_APPLIANCE_PRIOR: Final = "appliance_prior"
ATTR_OCCUPANCY_PRIOR: Final = "occupancy_prior"
