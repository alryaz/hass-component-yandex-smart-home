"""Support for Actions on Yandex Smart Home."""
__all__ = [

]

import logging
from ipaddress import IPv4Network, IPv6Network, collapse_addresses
from typing import Any, Dict, TYPE_CHECKING, Union, Sequence, List

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import CONF_NAME, CONF_ENTITY_ID, CONF_MAXIMUM, CONF_MINIMUM
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entityfilter as ef
from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from homeassistant.loader import bind_hass

from .const import (
    DOMAIN, CONF_ENTITY_CONFIG, CONF_FILTER, CONF_ROOM, CONF_TYPE,
    CONF_ENTITY_PROPERTIES, CONF_ATTRIBUTE, CONF_ENTITY_PROPERTY_TYPE,
    CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_RELATIVE_VOLUME_ONLY,
    CONF_INPUT_SOURCES, CONF_ENTITY_TOGGLES,
    CONF_SCRIPT_CHANNEL_UP, CONF_SCRIPT_CHANNEL_DOWN,
    ATTR_LAST_ACTION_TARGETS, ATTR_LAST_ACTION_TIME,
    ATTR_LAST_SYNC_TIME, DATA_CONFIG,
    CONF_DIAGNOSTICS_MODE, CONF_ENTITY_MODES, CONF_MAPPING, CONF_SET_SCRIPT, CONF_PROGRAMS, CONF_MULTIPLIER,
    CONF_ENTITY_RANGES, CONF_PRECISION, MODES_NUMERIC
)
from .core.helpers import Config, get_child_instances
from .core.http import YandexSmartHomeUnauthorizedView, YandexSmartHomeView
from .core.type_mapper import DOMAIN_TO_YANDEX_TYPES
from .functions.capability import CAPABILITIES, CAPABILITIES_TOGGLE, CAPABILITIES_MODE, CAPABILITIES_RANGE
from .functions.prop import PROPERTIES

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from .functions.capability import _ModeCapability

_LOGGER = logging.getLogger(__name__)

PROPERTY_INSTANCE_SCHEMA = vol.In(get_child_instances(PROPERTIES))
TOGGLE_INSTANCE_SCHEMA = vol.In(get_child_instances(CAPABILITIES, CAPABILITIES_TOGGLE))
MODE_INSTANCE_SCHEMA = vol.In(get_child_instances(CAPABILITIES, CAPABILITIES_MODE))
RANGE_INSTANCE_SCHEMA = vol.In(get_child_instances(CAPABILITIES, CAPABILITIES_RANGE))

ENTITY_PROPERTY_SCHEMA = vol.Any(
    vol.All(cv.entity_id, lambda x: {CONF_ENTITY_ID: x}),
    vol.Schema(
        {
            vol.Optional(CONF_ENTITY_ID): cv.entity_id,
            vol.Optional(CONF_ATTRIBUTE): cv.string,
        }
    )
)


def check_mode_override_mappings(value: Dict[str, Any]):
    for instance, config in value.items():
        if CONF_MAPPING not in config:
            continue

        capability: '_ModeCapability'
        for capability in CAPABILITIES:
            _LOGGER.debug('Check on %s with %s' % (capability.instance, instance))
            if capability.instance == instance:
                invalid_keys = config[CONF_MAPPING].keys() - set(capability.internal_modes)
                if invalid_keys:
                    raise vol.Invalid('Invalid Yandex modes for overrides: %s' % ', '.join(invalid_keys),
                                      path=[instance, CONF_MAPPING])
                break

    return value


NUMERIC_MODE_VALIDATOR = vol.In(MODES_NUMERIC)
NUMERIC_MODE_SCHEMA = vol.Any(
    cv.boolean,
    {NUMERIC_MODE_VALIDATOR: cv.string},
    vol.All([NUMERIC_MODE_VALIDATOR], vol.Length(min=2, max=10))
)
PROPERTY_OVERRIDES_SCHEMA = vol.All({PROPERTY_INSTANCE_SCHEMA: ENTITY_PROPERTY_SCHEMA})
TOGGLE_OVERRIDES_SCHEMA = vol.All({TOGGLE_INSTANCE_SCHEMA: cv.entity_id})
MODE_OVERRIDES_SCHEMA = vol.All(
    {
        MODE_INSTANCE_SCHEMA: vol.Schema({
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_SET_SCRIPT): cv.SCRIPT_SCHEMA,
            vol.Optional(CONF_MAPPING): {cv.string: vol.All(cv.ensure_list, [cv.string])},
        })
    },
    check_mode_override_mappings
)


def check_range_overrides(value: Dict[str, Any]):
    for instance, config in value.items():
        if config[CONF_MAXIMUM] <= config[CONF_MINIMUM]:
            raise vol.Invalid('Difference between min and max must be greater than 0',
                              path=[instance, CONF_MAXIMUM])

        if config[CONF_MULTIPLIER] == 0:
            raise vol.Invalid('Multiplier must be greater than 0',
                              path=[instance, CONF_MULTIPLIER])

    return value


RANGE_OVERRIDES_SCHEMA = vol.All(
    {
        RANGE_INSTANCE_SCHEMA: vol.Schema({
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_SET_SCRIPT): cv.SCRIPT_SCHEMA,
            vol.Optional(CONF_MINIMUM, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional(CONF_MAXIMUM, default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional(CONF_PRECISION, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Optional(CONF_MULTIPLIER, default=1): cv.small_float,
        })
    },
    check_range_overrides
)

ENTITY_SCHEMA = vol.Schema(
    {
        # Entity options
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_ROOM): cv.string,
        vol.Optional(CONF_TYPE): cv.string,

        # Additional options
        vol.Optional(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID): cv.boolean,
        vol.Optional(CONF_RELATIVE_VOLUME_ONLY): cv.boolean,
        vol.Optional(CONF_SCRIPT_CHANNEL_UP): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SCRIPT_CHANNEL_DOWN): cv.SCRIPT_SCHEMA,

        # Numeric mode capabilities
        # (True - enable automatic, False - disable, dictionary - custom modes)
        vol.Optional(CONF_INPUT_SOURCES): NUMERIC_MODE_SCHEMA,
        vol.Optional(CONF_PROGRAMS): NUMERIC_MODE_SCHEMA,

        # Overrides
        vol.Optional(CONF_ENTITY_PROPERTIES, default={}): PROPERTY_OVERRIDES_SCHEMA,
        vol.Optional(CONF_ENTITY_TOGGLES, default={}): TOGGLE_OVERRIDES_SCHEMA,
        vol.Optional(CONF_ENTITY_MODES, default={}): MODE_OVERRIDES_SCHEMA,
        vol.Optional(CONF_ENTITY_RANGES, default={}): RANGE_OVERRIDES_SCHEMA,
    }
)


def validate_networks(value: Union[bool, Sequence[str]]) -> Union[bool, List[Union[IPv6Network, IPv4Network]]]:
    if value is True:
        return [IPv4Network('0.0.0.0/0'), IPv6Network('::/0')]

    if not value:
        return []

    converted_networks_ipv4 = []
    converted_networks_ipv6 = []
    for i, network in enumerate(value):
        try:
            if ':' in value:
                converted_networks_ipv6.append(IPv6Network(network))
            else:
                converted_networks_ipv4.append(IPv4Network(network))
        except ValueError:
            raise vol.Invalid("invalid network provided", path=[i])

    if not converted_networks_ipv6:
        return list(collapse_addresses(converted_networks_ipv4))
    elif not converted_networks_ipv4:
        return list(collapse_addresses(converted_networks_ipv6))
    return [*collapse_addresses(converted_networks_ipv4), *collapse_addresses(converted_networks_ipv6)]


YANDEX_SMART_HOME_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_FILTER, default={}): ef.FILTER_SCHEMA,
        vol.Optional(CONF_ENTITY_CONFIG, default={}): {cv.entity_id: ENTITY_SCHEMA},
        vol.Optional(CONF_DIAGNOSTICS_MODE, default=False):
            vol.All(vol.Any(cv.boolean, vol.All(cv.ensure_list, [cv.string])), validate_networks),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: YANDEX_SMART_HOME_SCHEMA,
    },
    extra=vol.ALLOW_EXTRA
)


@callback
@bind_hass
def _register_views(hass: HomeAssistantType):
    # Register Yandex HTTP handlers
    _LOGGER.debug("Adding HomeAssistant Yandex views")
    hass.http.register_view(YandexSmartHomeUnauthorizedView)
    hass.http.register_view(YandexSmartHomeView)


async def async_setup(hass: HomeAssistantType, config: ConfigType):
    """Activate Yandex Smart Home component."""

    _register_views(hass)

    if DOMAIN not in config:
        return True

    # Save YAML config to data to use it later
    hass.data[DATA_CONFIG] = config[DOMAIN]

    # Find existing entry
    existing_entries = hass.config_entries.async_entries(DOMAIN)
    if existing_entries:
        if existing_entries[0].source == config_entries.SOURCE_IMPORT:
            _LOGGER.debug('Skipping existing import binding')
        else:
            _LOGGER.warning('YAML config is overridden by another config entry!')
        return True

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
    yandex_cfg = config_entry.data

    if config_entry.source == config_entries.SOURCE_IMPORT:
        yandex_cfg = hass.data.get(DATA_CONFIG)
        if not yandex_cfg:
            _LOGGER.info('Removing entry %s after removal from YAML configuration.' % config_entry.entry_id)
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
            return False

    else:
        yandex_cfg = YANDEX_SMART_HOME_SCHEMA(dict(yandex_cfg))

    # Check for diagnostics mode
    diagnostics_mode = yandex_cfg.get(CONF_DIAGNOSTICS_MODE)

    if diagnostics_mode:
        from homeassistant.components.persistent_notification import async_create as create_notification
        from custom_components.yandex_smart_home.core.http import YandexSmartHomeView

        warning_text = "Diagnostics mode is enabled. Your Yandex Smart home setup may become vulnerable to external " \
                       "unauthorized requests. Please, use with caution. Unauthorized requests from the following" \
                       " networks are currently allowed: %s" % (', '.join(map(str, diagnostics_mode)))

        contents_links = "Links (will open in a new tab):"

        for url in [YandexSmartHomeView.url] + YandexSmartHomeView.extra_urls:
            target_url = url
            contents_links += '\n- <a href="%s" target="_blank">%s</a>' % (target_url, url)

        contents_links += (
            '\n\nJSON Formatter extension for chromium-based browsers: '
            '<a href="https://chrome.google.com/webstore/detail/bcjindcccaagfpapjjmafapmmgkkhgoa" target="_blank">'
            'Chrome Web Store</a>, <a href="https://github.com/callumlocke/json-formatter" target="_blank">GitHub</a>'
        )

        create_notification(
            hass,
            warning_text + "\n\n" + contents_links,
            "Yandex Smart Home Diagnostics Mode",
            "yandex_smart_home_diagnostics_mode"
        )

        _LOGGER.warning(warning_text)

    # Create configuration object (and thus enable HTTP request serving)
    hass.data[DOMAIN] = Config(
        should_expose=yandex_cfg[CONF_FILTER],
        entity_config=yandex_cfg[CONF_ENTITY_CONFIG],
        diagnostics_mode=diagnostics_mode
    )

    # Create Yandex request statistics sensor
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(
            config_entry,
            SENSOR_DOMAIN
        )
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    
    # Remove Yandex request statistics sensor
    await hass.config_entries.async_forward_entry_unload(config_entry, SENSOR_DOMAIN)

    # Remove configuration object (and thus disable HTTP request serving)
    hass.data.pop(DOMAIN)

    return True
