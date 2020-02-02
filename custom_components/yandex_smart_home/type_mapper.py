"""Type mapper to infer yandex entity types from HomeAssistant's domains"""

from homeassistant.components import (
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

from .const import (
    TYPE_OTHER,
    TYPE_THERMOSTAT,
    TYPE_THERMOSTAT_AC,
    TYPE_OPENABLE_CURTAIN,
    TYPE_SWITCH,
    TYPE_LIGHT,
    TYPE_MEDIA_DEVICE,
    TYPE_VACUUM_CLEANER,
    TYPE_MEDIA_DEVICE_TV,
    TYPE_HUMIDIFIER,
    ATTR_MODEL,
    ATTR_TARGET_HUMIDITY
)

MAPPING_DEFAULT = "default"
DOMAIN_TO_YANDEX_TYPES = {
    binary_sensor.DOMAIN: TYPE_OTHER,
    camera.DOMAIN: TYPE_OTHER,
    climate.DOMAIN: {
        MAPPING_DEFAULT: TYPE_THERMOSTAT,
        TYPE_THERMOSTAT_AC: lambda h, s, c: s.attributes.get(ATTR_SUPPORTED_FEATURES) & climate.SUPPORT_SWING_MODE
    },
    cover.DOMAIN: TYPE_OPENABLE_CURTAIN,
    fan.DOMAIN: {
        MAPPING_DEFAULT: TYPE_THERMOSTAT,
        TYPE_HUMIDIFIER: [
            lambda h, s, c: s.attributes.get(ATTR_MODEL, '').startswith("zhimi.humidifier."),  # Xiaomi Humidifiers
            lambda h, s, c: s.attributes.get(ATTR_TARGET_HUMIDITY) is not None,  # WeMo Humidifiers
        ],
    },
    group.DOMAIN: TYPE_SWITCH,
    input_boolean.DOMAIN: TYPE_SWITCH,
    light.DOMAIN: TYPE_LIGHT,
    lock.DOMAIN: TYPE_OTHER,
    media_player.DOMAIN: {
        MAPPING_DEFAULT: TYPE_MEDIA_DEVICE,
        TYPE_MEDIA_DEVICE_TV: lambda h, s, c: s.attributes.get(ATTR_DEVICE_CLASS) == media_player.DEVICE_CLASS_TV,
    },
    scene.DOMAIN: TYPE_OTHER,
    script.DOMAIN: TYPE_OTHER,
    switch.DOMAIN: TYPE_SWITCH,
    vacuum.DOMAIN: TYPE_VACUUM_CLEANER,
}


def get_supported_types():
    supported_types = {}
    for domain, yandex_type in DOMAIN_TO_YANDEX_TYPES.items():
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
    yandex_type = DOMAIN_TO_YANDEX_TYPES.get(state.domain, TYPE_OTHER)
    if isinstance(yandex_type, dict):
        default_type = TYPE_OTHER
        for subtype, mapping_function in yandex_type.items():
            if subtype == MAPPING_DEFAULT:
                default_type = mapping_function
            elif isinstance(mapping_function, list):
                for func in mapping_function:
                    if func(hass, state, entity_config):
                        return subtype
            elif mapping_function(hass, state, entity_config):
                return subtype

        return default_type

    return yandex_type
