"""Constants for the WeMo Crockpot integration."""

DOMAIN = "wemo_crockpot"

# Crockpot mode values (numeric values sent to device)
MODE_OFF = "0"
MODE_WARM = "1"
MODE_LOW = "2"
MODE_HIGH = "3"

# Mode display names mapped to values
MODES = {
    MODE_OFF: "Off",
    MODE_WARM: "Warm",
    MODE_LOW: "Low",
    MODE_HIGH: "High",
}

# Reverse mapping: name to value
MODE_TO_VALUE = {
    "Off": MODE_OFF,
    "Warm": MODE_WARM,
    "Low": MODE_LOW,
    "High": MODE_HIGH,
}
