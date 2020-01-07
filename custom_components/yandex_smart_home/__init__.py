"""Support for Actions on Yandex Smart Home."""
import logging
from copy import deepcopy
from typing import Dict, Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entityfilter, config_validation as cv

from .const import (
    DOMAIN, CONF_ENTITY_CONFIG, CONF_FILTER, CONF_ROOM,
    CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_RELATIVE_VOLUME_ONLY,
    CONF_INPUT_SOURCES, MODES_NUMERIC, CONF_ENTITY_BACKLIGHT,
    CONF_SCRIPT_CHANNEL_UP, CONF_SCRIPT_CHANNEL_DOWN, CONF_EXPOSE_AS,
    DOMAIN_TO_YANDEX_TYPES)
from .helpers import Config
from .http import YandexSmartHomeUnauthorizedView, YandexSmartHomeView

_LOGGER = logging.getLogger(__name__)

ENTITY_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_ROOM): cv.string,
    vol.Optional(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID): cv.boolean,
    vol.Optional(CONF_RELATIVE_VOLUME_ONLY): cv.boolean,
    vol.Optional(CONF_INPUT_SOURCES): vol.Any(cv.boolean, {vol.In(MODES_NUMERIC):
                                                               cv.string}),
    vol.Optional(CONF_ENTITY_BACKLIGHT): cv.entity_id,
    vol.Optional(CONF_SCRIPT_CHANNEL_UP): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_SCRIPT_CHANNEL_DOWN): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_EXPOSE_AS): cv.string,
})

YANDEX_SMART_HOME_SCHEMA = vol.All(
    vol.Schema({
        vol.Optional(CONF_FILTER, default={}): entityfilter.FILTER_SCHEMA,
        vol.Optional(CONF_ENTITY_CONFIG, default={}): {cv.entity_id:
                                                           ENTITY_SCHEMA},
    }, extra=vol.PREVENT_EXTRA))

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: YANDEX_SMART_HOME_SCHEMA
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, yaml_config: Dict[str, Any]):
    """Activate Yandex Smart Home component."""

    hass.http.register_view(YandexSmartHomeUnauthorizedView)
    hass.http.register_view(YandexSmartHomeView)

    if DOMAIN not in yaml_config:
        return True

    import_conf = yaml_config[DOMAIN]

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=deepcopy(import_conf)
        )
    )

    return True


async def async_setup_entry(hass, config_entry):
    should_expose = config_entry.data.get(CONF_FILTER, {})
    _LOGGER.debug('async_setup_entry should_expose=%s', should_expose)
    entity_config = config_entry.data.get(CONF_ENTITY_CONFIG, {})
    _LOGGER.debug('async_setup_entry entity_config=%s', entity_config)

    hass.data[DOMAIN] = Config(
        should_expose=should_expose,
        entity_config=entity_config
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    hass.data.pop(DOMAIN)

    return True
