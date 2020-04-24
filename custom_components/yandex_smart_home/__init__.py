"""Support for Actions on Yandex Smart Home."""
import logging
from typing import Dict

import voluptuous as vol
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entityfilter as ef
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    DOMAIN, CONF_ENTITY_CONFIG, CONF_FILTER, CONF_ROOM, CONF_TYPE,
    CONF_ENTITY_PROPERTIES, CONF_ENTITY_PROPERTY_ENTITY,
    CONF_ENTITY_PROPERTY_ATTRIBUTE, CONF_ENTITY_PROPERTY_TYPE,
    CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_RELATIVE_VOLUME_ONLY,
    CONF_INPUT_SOURCES, MODES_NUMERIC, CONF_ENTITY_TOGGLES,
    CONF_SCRIPT_CHANNEL_UP, CONF_SCRIPT_CHANNEL_DOWN,
    ATTR_LAST_ACTION_TARGETS, ATTR_LAST_ACTION_TIME,
    ATTR_LAST_SYNC_TIME, DATA_YANDEX_SMART_HOME_CONFIG,
    CONF_DIAGNOSTICS_MODE
)
from .helpers import Config, get_child_instances
from .http import YandexSmartHomeUnauthorizedView, YandexSmartHomeView
from .type_mapper import DOMAIN_TO_YANDEX_TYPES
from .capability import _ToggleCapability
from .prop import _Property

_LOGGER = logging.getLogger(__name__)

ENTITY_PROPERTY_SCHEMA = vol.Any(
    vol.All(
        cv.entity_id,
        lambda x: {CONF_ENTITY_PROPERTY_ENTITY: x},
    ),
    vol.Schema(
        {
            vol.Optional(CONF_ENTITY_PROPERTY_ENTITY): cv.entity_id,
            vol.Optional(CONF_ENTITY_PROPERTY_ATTRIBUTE): cv.string,
        }
    )
)

PROPERTY_INSTANCE_SCHEMA = vol.In(get_child_instances(_Property))
TOGGLE_INSTANCE_SCHEMA = vol.In(get_child_instances(_ToggleCapability))

ENTITY_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ROOM): cv.string,
        vol.Optional(CONF_TYPE): cv.string,
        vol.Optional(CONF_ENTITY_PROPERTIES, default={}): {PROPERTY_INSTANCE_SCHEMA: ENTITY_PROPERTY_SCHEMA},
        vol.Optional(CONF_ENTITY_TOGGLES, default={}): {TOGGLE_INSTANCE_SCHEMA: cv.entity_id},
        vol.Optional(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID): cv.boolean,
        vol.Optional(CONF_RELATIVE_VOLUME_ONLY): cv.boolean,
        vol.Optional(CONF_INPUT_SOURCES, default=True): vol.Any(cv.boolean, {vol.In(MODES_NUMERIC): cv.string}),
        vol.Optional(CONF_SCRIPT_CHANNEL_UP): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SCRIPT_CHANNEL_DOWN): cv.SCRIPT_SCHEMA,
    }
)

YANDEX_SMART_HOME_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_FILTER, default={}): ef.FILTER_SCHEMA,
        vol.Optional(CONF_ENTITY_CONFIG, default={}): {cv.entity_id: ENTITY_SCHEMA},
        vol.Optional(CONF_DIAGNOSTICS_MODE, default=False): cv.boolean,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: YANDEX_SMART_HOME_SCHEMA,
    },
    extra=vol.ALLOW_EXTRA
)

async def async_setup(hass: HomeAssistantType, config: Dict):
    """Activate Yandex Smart Home component."""
    
    # Register Yandex HTTP handlers
    _LOGGER.debug("Adding HomeAssistant Yandex views")
    hass.http.register_view(YandexSmartHomeUnauthorizedView)
    hass.http.register_view(YandexSmartHomeView)

    if DOMAIN not in config:
        return True

    # Save YAML config to data to use it later
    hass.data[DATA_YANDEX_SMART_HOME_CONFIG] = config[DOMAIN]

    # Forward configuration setup to config flow
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={}
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry):
    if DATA_YANDEX_SMART_HOME_CONFIG in hass.data:
        if config_entry.source != SOURCE_IMPORT:
            _LOGGER.warning('Integration set up in HomeAssistant attempts to override existing YAML configuration.')
            return False
            
        # Get config from YAML data
        config = hass.data[DATA_YANDEX_SMART_HOME_CONFIG]
        
        # Get pre-made entity filter
        should_expose = config[CONF_FILTER]
        
    elif config_entry.source == SOURCE_IMPORT:
        _LOGGER.debug('Removing config entry from HASS as it was from YAML and now missing')
        hass.async_create_task(
            hass.config_entries.async_remove(
                config_entry.entry_id
            )
        )
        return False
        
    else:
        # Get config from entry data
        config = config_entry.data
        
        # Generate entity filter from config dictionary
        should_expose = ef._convert_filter(config[CONF_FILTER])

    # Get entity config from configuration
    entity_config = config.get(CONF_ENTITY_CONFIG, {})

    # Check for diagnostics mode
    diagnostics_mode = config.get(CONF_DIAGNOSTICS_MODE)
    if diagnostics_mode:
        from homeassistant.components.persistent_notification import async_create as create_notification
        from .http import YandexSmartHomeView

        contents = "Diagnostics mode is enabled. Your Yandex Smart home setup will become vulnerable to external unauthorized requests. Please, use with caution."
        
        contents_links = "Links (will open in a new tab):"
        base_url = hass.config.api.base_url
        for url in [YandexSmartHomeView.url] + YandexSmartHomeView.extra_urls:
            target_url = base_url + url if base_url else url
            contents_links += '\n- <a href="%s" target="_blank">%s</a>' % (target_url, url)
        contents_links += (
            '\n\nJSON Formatter extension for chromium-based browsers: '
            '<a href="https://chrome.google.com/webstore/detail/bcjindcccaagfpapjjmafapmmgkkhgoa" target="_blank">Chrome Web Store</a>, '
            '<a href="https://github.com/callumlocke/json-formatter" target="_blank">GitHub</a>'
        )

        create_notification(
            hass,
            contents + "\n\n" + contents_links,
            "Yandex Smart Home Diagnostics Mode",
            "yandex_smart_home_diagnostics_mode"
        )
        _LOGGER.warning(contents)

    # Create configuration object (and thus enable HTTP request serving)
    hass.data[DOMAIN] = Config(
        should_expose=should_expose,
        entity_config=entity_config,
        diagnostics_mode=diagnostics_mode
    )

    # Create Yandex request statistics sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, SENSOR_DOMAIN)
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    
    # Remove Yandex request statistics sensor
    await hass.config_entries.async_forward_entry_unload(config_entry, SENSOR_DOMAIN)

    # Remove configuration object (and thus disable HTTP request serving)
    hass.data.pop(DOMAIN)

    return True
