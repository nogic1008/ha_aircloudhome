"""Constants for aircloudhome."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Integration metadata
DOMAIN = "aircloudhome"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

# Platform parallel updates - applied to all platforms
PARALLEL_UPDATES = 1

# Default configuration values
DEFAULT_UPDATE_INTERVAL_MINUTES = 5
DEFAULT_ENABLE_DEBUGGING = False

# Configuration option keys
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"
