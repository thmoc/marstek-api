"""Constants for the Marstek Local API integration."""

from datetime import timedelta

DOMAIN = "marstek_local"

DEFAULT_PORT = 30000
SCAN_INTERVAL = timedelta(seconds=30)

MODE_AUTO = "Auto"
MODE_AI = "AI"
MODE_MANUAL = "Manual"
MODE_PASSIVE = "Passive"
MODE_UPS = "UPS"
MODES = [MODE_AUTO, MODE_AI, MODE_MANUAL, MODE_PASSIVE, MODE_UPS]

# Hard safety limit for passive mode power (W). Device maximum is 2500 W.
MAX_POWER = 2500
DEFAULT_PASSIVE_DURATION = 300

SERVICE_SET_PASSIVE = "set_passive_mode"
SERVICE_SET_MANUAL = "set_manual_schedule"
