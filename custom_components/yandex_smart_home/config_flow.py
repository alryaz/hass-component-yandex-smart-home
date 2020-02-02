"""Config flow for the Yandex Smart Home component."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import (
    media_player,
    switch,
    light
)
from homeassistant.config import YAML_CONFIG_FILE
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.core import valid_entity_id
from homeassistant.helpers import entityfilter as ef

from .const import (
    DOMAIN, CONF_FILTER, CONF_ENTITY_CONFIG,
    TYPE_OTHER, CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_ENTITY_BACKLIGHT,
    CONF_EXPOSE_AS, PREFIX_TYPES)  # pylint: disable=unused-import
from .type_mapper import get_supported_types, DOMAIN_TO_YANDEX_TYPES

CONF_CUSTOMIZE_EXPOSURE = "customize_exposure"
YANDEX_DEVICE_SUBTYPES = sorted(map(lambda x: x.replace(PREFIX_TYPES, ''), get_supported_types()))

_LOGGER = logging.getLogger(__name__)


def diff(first, second):
    second = set(second)
    return [item for item in first if item not in second]


class YandexSmartHomeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Yandex Smart Home."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def __init__(self):
        """Initialize."""
        super().__init__()

        self._user_input = None
        self._filter_config = None
        self._entity_config = None
        self._last_custom_entity_id = None

        self.supported_schema = {}
        self.unsupported_schema = {}
        for domain, yandex_type in DOMAIN_TO_YANDEX_TYPES.items():
            key = 'domain_' + domain
            if yandex_type == TYPE_OTHER:
                self.unsupported_schema[vol.Optional(key, default=False)] = bool
            else:
                self.supported_schema[vol.Optional(key, default=True)] = bool

        _LOGGER.debug('-> supported_schema %s' % self.supported_schema)
        _LOGGER.debug('-> unsupported_schema %s' % self.unsupported_schema)

        self.entities_schema = {
            vol.Optional(ef.CONF_INCLUDE_ENTITIES, default=''): str,
            vol.Optional(ef.CONF_EXCLUDE_ENTITIES, default=''): str,
            vol.Optional(CONF_CUSTOMIZE_EXPOSURE, default=False): bool,
        }

    def generate_custom_exposure_schema(self, entity_id):
        domain = entity_id.split('.')[0]
        schema = {
            vol.Optional(CONF_EXPOSE_AS): vol.In(YANDEX_DEVICE_SUBTYPES),
        }
        if domain in (media_player.DOMAIN, light.DOMAIN, switch.DOMAIN):
            schema[vol.Optional(CONF_ENTITY_BACKLIGHT)] = str

        entity = self.hass.states.get(entity_id)
        if entity:
            features = entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
            if domain == media_player.DOMAIN and features & media_player.SUPPORT_PLAY_MEDIA != 0:
                schema[vol.Optional(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, default=False)] = bool

        return schema

    @classmethod
    def custom_exposure_schema_errors(cls, entity_config):
        errors = []
        if CONF_ENTITY_BACKLIGHT in entity_config and not valid_entity_id(entity_config[CONF_ENTITY_BACKLIGHT]):
            errors.append(CONF_ENTITY_BACKLIGHT)

        if errors:
            return {key: "invalid_" + key for key in errors}
        else:
            return None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        _LOGGER.debug('async_step_user %s' % user_input)

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if not user_input or any([key not in user_input for key in self.supported_schema]):
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(self.supported_schema),
                errors={},
            )

        self._user_input = user_input

        if self.unsupported_schema:
            return await self.async_step_unsupported()
        else:
            return await self.async_step_selective()

    async def async_step_unsupported(self, user_input=None):
        """Step: Configure unsupported devices"""
        if not user_input or any([key not in user_input for key in self.unsupported_schema.keys()]):
            return self.async_show_form(
                step_id="unsupported",
                data_schema=vol.Schema(self.unsupported_schema),
                errors={},
            )

        if self._user_input:
            self._user_input.update(user_input)
        else:
            _LOGGER.error('New _user_input is required. Something is wrong.')
            self._user_input = user_input

        return await self.async_step_selective()

    async def async_step_selective(self, user_input=None):
        """Step: Select entities to include/exclude"""

        def show_form(error=None):
            return self.async_show_form(
                step_id="selective",
                data_schema=vol.Schema(self.entities_schema),
                errors={} if not error else {"base": error}
            )

        if not user_input or ef.CONF_EXCLUDE_ENTITIES not in user_input or ef.CONF_INCLUDE_ENTITIES not in user_input:
            return show_form()

        if self._user_input:
            self._user_input.update(user_input)
        else:
            _LOGGER.error('New _user_input is required. Something is wrong.')
            self._user_input = user_input

        filter_config = {
            ef.CONF_INCLUDE_DOMAINS: [],
            ef.CONF_EXCLUDE_DOMAINS: [],  # this will remain empty
            ef.CONF_INCLUDE_ENTITIES: [],
            ef.CONF_EXCLUDE_ENTITIES: []
        }

        for key, val in self._user_input.items():
            if key.startswith('domain_'):
                domain = key[7:]
                if val:
                    filter_config[ef.CONF_INCLUDE_DOMAINS].append(domain)

            elif key in (ef.CONF_EXCLUDE_ENTITIES, ef.CONF_INCLUDE_ENTITIES):
                val = val.replace(' ', '')
                if val:
                    for entity_id in val.split(','):
                        if valid_entity_id(entity_id):
                            filter_config[key].append(entity_id)
                        else:
                            return show_form("invalid_entity_id" if entity_id else "empty_entity_id")

        if not filter_config[ef.CONF_INCLUDE_DOMAINS] and not filter_config[ef.CONF_INCLUDE_ENTITIES]:
            return show_form("empty_includes")

        if any(x in filter_config[ef.CONF_INCLUDE_ENTITIES] for x in filter_config[ef.CONF_EXCLUDE_ENTITIES]):
            return show_form("conflicting_entity_includes")

        _LOGGER.debug('filter_config %s', filter_config)
        _LOGGER.debug('user_input %s', user_input)

        self._filter_config = filter_config
        self._entity_config = {}

        if user_input[CONF_CUSTOMIZE_EXPOSURE]:
            return await self.async_step_custom()
        else:
            return self._create_entry()

    async def async_step_custom(self, user_input=None):
        if user_input:
            errors = self.custom_exposure_schema_errors(user_input)
            if errors:
                schema = vol.Schema(self.generate_custom_exposure_schema(self._last_custom_entity_id))
                return self.async_show_form(
                    step_id="custom",
                    data_schema=schema,
                    description_placeholders={"entity_id": self._last_custom_entity_id},
                    errors=errors
                )

            self._entity_config[self._last_custom_entity_id] = user_input

        next_entity = None
        custom_exposure_schema = None
        for filter_entity in self._filter_config[ef.CONF_INCLUDE_ENTITIES]:
            if filter_entity not in self._entity_config:
                custom_exposure_schema = self.generate_custom_exposure_schema(filter_entity)
                if custom_exposure_schema:
                    next_entity = filter_entity
                    break

        if not user_input and next_entity:
            self._last_custom_entity_id = next_entity
            return self.async_show_form(
                step_id="custom",
                data_schema=vol.Schema(custom_exposure_schema),
                description_placeholders={"entity_id": next_entity}
            )

        return self._create_entry()

    def _create_entry(self):
        return self.async_create_entry(
            title=f'Default',
            data={
                CONF_FILTER: self._filter_config,
                CONF_ENTITY_CONFIG: self._entity_config
            },
        )

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        if self._async_current_entries():
            _LOGGER.warning("Only one configuration of Yandex Smart Home is allowed.")
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title=YAML_CONFIG_FILE,
            data={},
            description='Configuration imported from YAML'
        )
