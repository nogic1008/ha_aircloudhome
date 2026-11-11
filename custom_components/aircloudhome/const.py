"""Constants for aircloudhome."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Integration metadata
DOMAIN = "aircloudhome"
ATTRIBUTION = "Data provided by AirCloud Home (Hitachi)"

# Platform parallel updates - applied to all platforms
PARALLEL_UPDATES = 1

# Default configuration values
DEFAULT_UPDATE_INTERVAL_MINUTES = 5
DEFAULT_ENABLE_DEBUGGING = False

# Configuration data keys
# Cloud region of the account (see AirCloudHomeRegion). Entries created before
# region support have no value and use the Japan API.
CONF_REGION = "region"

# Configuration option keys
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"
