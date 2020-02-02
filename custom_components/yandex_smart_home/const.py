"""Constants for Yandex Smart Home."""
DOMAIN = 'yandex_smart_home'

DATA_YANDEX_SMART_HOME_CONFIG = DOMAIN + "_config"

CONF_ENTITY_CONFIG = 'entity_config'
CONF_FILTER = 'filter'
CONF_ROOM = 'room'
CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID = 'channel_set_via_media_content_id'
CONF_RELATIVE_VOLUME_ONLY = 'relative_volume_only'
CONF_INPUT_SOURCES = 'sources'
CONF_CONTROLS_SWITCH = 'controls_switch'
CONF_ENTITY_BACKLIGHT = 'backlight'
CONF_SCRIPT_CHANNEL_UP = 'channel_up'
CONF_SCRIPT_CHANNEL_DOWN = 'channel_down'
CONF_EXPOSE_AS = 'expose_as'

ATTR_LAST_ACTION_TIME = "last_command_time"
ATTR_LAST_ACTION_TARGETS = "last_command_targets"
ATTR_LAST_SYNC_TIME = "last_sync_time"
ATTR_SYNCED_DEVICES_COUNT = "synced_devices_count"
ATTR_MODEL = "model"
ATTR_TARGET_HUMIDITY = "target_humidity"

# Yandex device types
# https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-types-docpage/
PREFIX_TYPES = 'devices.types.'
TYPE_LIGHT = PREFIX_TYPES + 'light'
TYPE_SOCKET = PREFIX_TYPES + 'socket'
TYPE_SWITCH = PREFIX_TYPES + 'switch'
TYPE_THERMOSTAT = PREFIX_TYPES + 'thermostat'
TYPE_THERMOSTAT_AC = PREFIX_TYPES + 'thermostat.ac'
TYPE_MEDIA_DEVICE = PREFIX_TYPES + 'media_device'
TYPE_MEDIA_DEVICE_TV = PREFIX_TYPES + 'media_device.tv'
TYPE_OPENABLE = PREFIX_TYPES + 'openable'
TYPE_OPENABLE_CURTAIN = PREFIX_TYPES + 'openable.curtain'
TYPE_HUMIDIFIER = PREFIX_TYPES + 'humidifier'
TYPE_PURIFIER = PREFIX_TYPES + 'purifier'
TYPE_VACUUM_CLEANER = PREFIX_TYPES + 'vacuum_cleaner'
TYPE_COOKING = PREFIX_TYPES + 'cooking'
TYPE_COOKING_COFFEE_MAKER = PREFIX_TYPES + 'cooking.coffee_maker'
TYPE_COOKING_KETTLE = PREFIX_TYPES + 'cooking.kettle'
TYPE_OTHER = PREFIX_TYPES + 'other'

# Error codes
# https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/response-codes-docpage/
ERR_DEVICE_UNREACHABLE = "DEVICE_UNREACHABLE"
ERR_DEVICE_NOT_FOUND = "DEVICE_NOT_FOUND"
ERR_INTERNAL_ERROR = 'INTERNAL_ERROR'
ERR_INVALID_ACTION = 'INVALID_ACTION'
ERR_INVALID_VALUE = 'INVALID_VALUE'
ERR_NOT_SUPPORTED_IN_CURRENT_MODE = 'NOT_SUPPORTED_IN_CURRENT_MODE'

# Event types
EVENT_ACTION_RECEIVED = 'yandex_smart_home_action'
EVENT_QUERY_RECEIVED = 'yandex_smart_home_query'
EVENT_DEVICES_RECEIVED = 'yandex_smart_home_devices'

MODES_NUMERIC = {
    'one', 'two', 'three', 'four', 'five',
    'six', 'seven', 'eight', 'nine', 'ten'
}
