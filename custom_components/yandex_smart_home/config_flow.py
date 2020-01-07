"""Config flow for the Yandex Smart Home component."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config import YAML_CONFIG_FILE
from homeassistant.core import valid_entity_id
from homeassistant.helpers import entityfilter as ef

from .const import DOMAIN, CONF_FILTER, CONF_ENTITY_CONFIG, DOMAIN_TO_YANDEX_TYPES, \
    TYPE_OTHER  # pylint: disable=unused-import

CONF_IGNORE_DOMAINS = "ignore_domains"
CONF_IGNORE_ENTITIES = "ignore_entities"

FILTER_TYPE_DOMAINS = vol.In([ef.CONF_INCLUDE_DOMAINS, ef.CONF_EXCLUDE_DOMAINS, CONF_IGNORE_DOMAINS])
FILTER_TYPE_ENTITIES = vol.In([ef.CONF_INCLUDE_ENTITIES, ef.CONF_EXCLUDE_ENTITIES, CONF_IGNORE_ENTITIES])

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
            vol.Optional(ef.CONF_EXCLUDE_ENTITIES, default=''): str
        }

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

        entity_config = {}
        # @TODO: entity configuration interface

        _LOGGER.debug('user_input before entry creation: %s', user_input)
        _LOGGER.debug('filter_config %s', filter_config)
        return self.async_create_entry(
            title=f'Default',
            data={
                CONF_FILTER: filter_config,
                CONF_ENTITY_CONFIG: entity_config
            },
        )

    async def async_step_import(self, import_config):
        _LOGGER.debug('async_step_import %s' % import_config)
        """Import a config entry from configuration.yaml."""
        if self._async_current_entries():
            _LOGGER.warning("Only one configuration of Yandex Smart Home is allowed.")
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title=YAML_CONFIG_FILE,
            data=import_config,
            description='Configuration imported from YAML'
        )
