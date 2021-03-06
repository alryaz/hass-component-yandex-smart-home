"""Type mapper to infer yandex entity types from HomeAssistant's domains"""

from homeassistant.components import (
    automation,
    binary_sensor,
    camera,
    climate,
    cover,
    fan,
    group,
    input_boolean,
    light,
    lock,
    media_player,
    scene,
    script,
    switch,
    vacuum,
)
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_SUPPORTED_FEATURES
from homeassistant.core import State
from homeassistant.helpers.typing import HomeAssistantType

from ..const import (
    TYPE_OTHER,
    TYPE_THERMOSTAT,
    TYPE_THERMOSTAT_AC,
    TYPE_OPENABLE,
    TYPE_OPENABLE_CURTAIN,
    TYPE_SWITCH,
    TYPE_SOCKET,
    TYPE_LIGHT,
    TYPE_MEDIA_DEVICE,
    TYPE_MEDIA_DEVICE_TV_BOX,
    TYPE_VACUUM_CLEANER,
    TYPE_MEDIA_DEVICE_TV,
    TYPE_HUMIDIFIER,
    ATTR_MODEL,
    ATTR_TARGET_HUMIDITY,
    DEVICE_CLASS_ANDROIDTV,
    DEVICE_CLASS_FIRETV,
    ATTR_YANDEX_TYPE,
)

MAPPING_DEFAULT = "default"
DOMAIN_TO_YANDEX_TYPES = {
    automation.DOMAIN: TYPE_OTHER,
    binary_sensor.DOMAIN: TYPE_OTHER,
    camera.DOMAIN: TYPE_OTHER,
    climate.DOMAIN: {
        MAPPING_DEFAULT: TYPE_THERMOSTAT,
        TYPE_THERMOSTAT_AC: lambda h, s, c: s.attributes.get(ATTR_SUPPORTED_FEATURES) & climate.SUPPORT_SWING_MODE
    },
    cover.DOMAIN: {
        MAPPING_DEFAULT: TYPE_OPENABLE,
        TYPE_OPENABLE_CURTAIN: [
            cover.DEVICE_CLASS_SHADE,
            cover.DEVICE_CLASS_SHUTTER,
            cover.DEVICE_CLASS_CURTAIN,
            cover.DEVICE_CLASS_BLIND,
            cover.DEVICE_CLASS_AWNING,
        ]
    },
    fan.DOMAIN: {
        MAPPING_DEFAULT: TYPE_THERMOSTAT,
        TYPE_HUMIDIFIER: lambda h, s, c: (
                s.attributes.get(ATTR_MODEL, '').startswith("zhimi.humidifier.") or  # Xiaomi Humidifiers
                s.attributes.get(ATTR_TARGET_HUMIDITY) is not None  # WeMo Humidifiers
        )
    },
    group.DOMAIN: TYPE_SWITCH,
    input_boolean.DOMAIN: TYPE_SWITCH,
    light.DOMAIN: TYPE_LIGHT,
    lock.DOMAIN: TYPE_OPENABLE,
    media_player.DOMAIN: {
        MAPPING_DEFAULT: TYPE_MEDIA_DEVICE,
        TYPE_MEDIA_DEVICE_TV: [
            media_player.DEVICE_CLASS_TV,
        ],
        TYPE_MEDIA_DEVICE_TV_BOX: [
            DEVICE_CLASS_ANDROIDTV,
            DEVICE_CLASS_FIRETV
        ],
    },
    scene.DOMAIN: TYPE_OTHER,
    script.DOMAIN: TYPE_OTHER,
    switch.DOMAIN: {
        MAPPING_DEFAULT: TYPE_SWITCH,
        TYPE_SOCKET: [switch.DEVICE_CLASS_OUTLET],
    },
    vacuum.DOMAIN: TYPE_VACUUM_CLEANER,
}


def get_supported_types():
    supported_types = {}
    for _, yandex_type in DOMAIN_TO_YANDEX_TYPES.items():
        if isinstance(yandex_type, dict):
            for key, val in yandex_type.items():
                if key == MAPPING_DEFAULT:
                    supported_types[val] = True
                else:
                    supported_types[key] = True
        else:
            supported_types[yandex_type] = True

    return supported_types.keys()


def determine_state_type(hass: HomeAssistantType, state: State, entity_config):
    """Yandex type based on domain and device class."""
    if ATTR_YANDEX_TYPE in state.attributes:
        return state.attributes[ATTR_YANDEX_TYPE]
        
    default_type = TYPE_OTHER
    yandex_type = DOMAIN_TO_YANDEX_TYPES.get(state.domain)
    if isinstance(yandex_type, dict):
        for subtype, mapping_function in yandex_type.items():
            if subtype == MAPPING_DEFAULT:
                default_type = mapping_function

            elif callable(mapping_function):
                if mapping_function(hass, state, entity_config):
                    return subtype

            else:
                device_class = state.attributes.get(ATTR_DEVICE_CLASS)
                if device_class in mapping_function:
                    return subtype

    elif isinstance(yandex_type, str):
        return yandex_type

    return default_type
