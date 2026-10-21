"""Constants for the Kerb integration."""

from __future__ import annotations

DOMAIN = "kerb"
STORAGE_KEY = f"{DOMAIN}.state"
STORAGE_VERSION = 1
CONFIG_VERSION = 1
EVENT_TYPE = f"{DOMAIN}_event"

# Config entry data (one entry per child).
CONF_NAME = "name"
CONF_AGE_BAND = "age_band"
CONF_CHILD_ID = "child_id"
CONF_DEVICES = "devices"
CONF_GUARDIANS = "guardians"
CONF_PIN_HASH = "pin_hash"
CONF_PIN = "pin"

# Per device.
CONF_DEVICE_ID = "id"
CONF_DEVICE_NAME = "name"
CONF_PLATFORM = "platform"
CONF_NETWORK_SWITCHES = "network_switches"
CONF_NETWORK_INVERTED = "network_inverted"
CONF_POWER_SWITCH = "power_switch"
CONF_GRACEFUL_OFF = "graceful_off"
CONF_POWER_OPT_IN = "power_opt_in"
CONF_POWER_DELAY = "power_delay_s"
CONF_IN_USE_ENTITY = "in_use_entity"
CONF_MANUAL = "manual"
CONF_ADD_ANOTHER = "add_another"

# Options.
CONF_ALLOWANCE = "allowance_minutes"
CONF_ALLOWANCE_DAYS = (
	"allowance_mon",
	"allowance_tue",
	"allowance_wed",
	"allowance_thu",
	"allowance_fri",
	"allowance_sat",
	"allowance_sun",
)
CONF_BEDTIME_START = "bedtime_start"
CONF_BEDTIME_END = "bedtime_end"
CONF_GRANT_CAP = "grant_cap_minutes_per_day"
CONF_CONFIRMATION_WINDOW = "confirmation_window_s"
CONF_LOW_THRESHOLD = "low_threshold_minutes"
CONF_RETENTION_DAYS = "usage_retention_days"

DEFAULT_ALLOWANCE = 120
DEFAULT_CONFIRMATION_WINDOW = 120
DEFAULT_LOW_THRESHOLD = 15
DEFAULT_RETENTION_DAYS = 31
DEFAULT_POWER_DELAY = 20
TICK_SECONDS = 60
# How long the dashboard stays armed for a guardian after they enter the PIN.
PIN_ARM_SECONDS = 300

# Services.
SERVICE_LOCK = "lock"
SERVICE_UNLOCK = "unlock"
SERVICE_GRANT = "grant"
SERVICE_SET_ALLOWANCE_TODAY = "set_allowance_today"
SERVICE_RECONCILE = "reconcile"
SERVICE_CONFIRM_MANUAL = "confirm_manual"

ATTR_CHILD = "child"
ATTR_DEVICE = "device"
ATTR_DURATION = "duration"
ATTR_SCOPE = "scope"
ATTR_MODE = "mode"
ATTR_REASON = "reason"
ATTR_SOURCE = "source"
ATTR_MINUTES = "minutes"
ATTR_PIN = "pin"

GRANT_BUTTONS = (15, 30, 60)
