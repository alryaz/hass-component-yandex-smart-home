"""Support for Actions on Yandex Smart Home."""
import logging
from copy import deepcopy
from typing import Optional

import voluptuous as vol
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_NAME
from homeassistant.helpers import entityfilter as ef, config_validation as cv
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    DOMAIN, CONF_ENTITY_CONFIG, CONF_FILTER, CONF_ROOM,
    CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_RELATIVE_VOLUME_ONLY,
    CONF_INPUT_SOURCES, MODES_NUMERIC, CONF_ENTITY_BACKLIGHT,
    CONF_SCRIPT_CHANNEL_UP, CONF_SCRIPT_CHANNEL_DOWN, CONF_EXPOSE_AS,
    ATTR_LAST_ACTION_TARGETS, ATTR_LAST_ACTION_TIME,
    ATTR_LAST_SYNC_TIME, DATA_YANDEX_SMART_HOME_CONFIG
)
from .helpers import Config
from .http import YandexSmartHomeUnauthorizedView, YandexSmartHomeView
from .type_mapper import DOMAIN_TO_YANDEX_TYPES

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

FILTER_SCHEMA = vol.Schema({
    vol.Optional(ef.CONF_INCLUDE_ENTITIES, default=[]): cv.entity_ids,
    vol.Optional(ef.CONF_EXCLUDE_ENTITIES, default=[]): cv.entity_ids,
    vol.Optional(ef.CONF_INCLUDE_DOMAINS, default=[]): vol.All(cv.ensure_list, [vol.In(DOMAIN_TO_YANDEX_TYPES.keys())]),
    vol.Optional(ef.CONF_EXCLUDE_DOMAINS, default=[]): vol.All(cv.ensure_list, [cv.string]),
})

YANDEX_SMART_HOME_SCHEMA = vol.All(
    vol.Schema({
        vol.Optional(CONF_FILTER, default={}): FILTER_SCHEMA,
        vol.Optional(CONF_ENTITY_CONFIG, default={}): {cv.entity_id: ENTITY_SCHEMA},
    }, extra=vol.PREVENT_EXTRA))

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: YANDEX_SMART_HOME_SCHEMA
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistantType, config: Optional[dict]):
    """Activate Yandex Smart Home component."""
    _LOGGER.debug("Adding HomeAssistant views")
    hass.http.register_view(YandexSmartHomeUnauthorizedView)
    hass.http.register_view(YandexSmartHomeView)

    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=deepcopy(conf)
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: Optional[ConfigEntry]):
    config = config_entry.data
    if DATA_YANDEX_SMART_HOME_CONFIG in hass.data:
        config = {**config, **hass.data[DATA_YANDEX_SMART_HOME_CONFIG]}

    hass.data[DATA_YANDEX_SMART_HOME_CONFIG] = config_entry

    filter_config = config.get(CONF_FILTER, {})
    should_expose = ef.generate_filter(
        include_domains=filter_config.get(ef.CONF_INCLUDE_DOMAINS, []),
        exclude_domains=filter_config.get(ef.CONF_EXCLUDE_DOMAINS, []),
        include_entities=filter_config.get(ef.CONF_INCLUDE_ENTITIES, []),
        exclude_entities=filter_config.get(ef.CONF_EXCLUDE_ENTITIES, [])
    )
    _LOGGER.debug('async_setup_entry filter_config=%s', filter_config)

    entity_config = config_entry.data.get(CONF_ENTITY_CONFIG, {})
    _LOGGER.debug('async_setup_entry entity_config=%s', entity_config)

    hass.data[DOMAIN] = Config(should_expose=should_expose, entity_config=entity_config)

    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, SENSOR_DOMAIN)
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(config_entry, SENSOR_DOMAIN)

    hass.data.pop(DOMAIN)

    return True
