"""Config flow for the Yandex Smart Home component."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import (
    media_player,
    script,
    sensor
)
from homeassistant.config import YAML_CONFIG_FILE
from homeassistant.core import valid_entity_id
from homeassistant.helpers import entityfilter as ef

from .const import (
    DOMAIN, CONF_FILTER, CONF_ENTITY_CONFIG,
    TYPE_OTHER, CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_TYPE,
    PREFIX_TYPES, CONF_ENTITY_PROPERTIES, CONF_ENTITY_TOGGLES)  # pylint: disable=unused-import
from .type_mapper import get_supported_types, DOMAIN_TO_YANDEX_TYPES
from .capability import _ToggleCapability

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

        self._custom_entities_remaining = None
        self._custom_entity_id = None
        self._custom_entity_config = None

        self._available_toggles = None
        self._available_properties = None

        self.supported_schema = {}
        self.unsupported_schema = {}

        # Generate lists of domains for exposure
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

    def _pre_step_check(self):
        if self._user_input is None:
            _LOGGER.error('Configuration flow is corrupted.')
            return "session_error"

        if self._async_current_entries():
            return "single_instance_allowed"

    async def async_step_user(self, user_input=None):
        """Step 1: Handle a flow initialized by the user."""
        _LOGGER.debug('async_step_user %s' % user_input)

        reason = self._pre_step_check()
        if reason:
            self.async_abort(reason=reason)

        if user_input is None:
            # Show form with a list of supported domains
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(self.supported_schema),
                errors={},
            )

        self._user_input = {
            CONF_FILTER: {},
            CONF_ENTITY_CONFIG: {},
        }

        included_domains = [
            domain[7:]
            for domain, choice in user_input.items()
            if choice is True
        ]

        if included_domains:
            self._user_input[CONF_FILTER] = {
                ef.CONF_INCLUDE_DOMAINS: included_domains
            }

        if self.unsupported_schema:
            return await self.async_step_unsupported()
        else:
            return await self.async_step_selective()

    async def async_step_unsupported(self, user_input=None):
        """Step 2: Enable unsupported domains on demand."""
        _LOGGER.debug('async_step_unsupported %s' % user_input)

        reason = self._pre_step_check()
        if reason:
            self.async_abort(reason=reason)

        #if not user_input or any([key not in user_input for key in self.unsupported_schema.keys()]):
        if user_input is None:
            # Show form with a list of unsupported domains
            return self.async_show_form(
                step_id="unsupported",
                data_schema=vol.Schema(self.unsupported_schema),
                errors={},
            )
        
        included_domains = [
            domain[7:]
            for domain, choice in user_input.items()
            if choice is True
        ]

        if included_domains:
            self._user_input[CONF_FILTER]\
                .setdefault(ef.CONF_INCLUDE_DOMAINS, [])\
                .extend(included_domains)

        if self._user_input[CONF_FILTER]:
            await self.async_step_selective()
        else:
            await self.async_step_without_domains()

    async def async_step_without_domains(self, user_input=None):
        """Step 3: Check whether the user intended the no-domains-added approach."""
        CONF_EXCLUDE_DOMAINS = "exclude_domains"

        reason = self._pre_step_check()
        if reason:
            self.async_abort(reason=reason)

        if not user_input:
            return self.async_show_form(
                step_id="without_domains",
                data_schema=vol.Schema({
                    vol.Required(CONF_EXCLUDE_DOMAINS, default=False): bool,
                })
            )
        
        if user_input[CONF_EXCLUDE_DOMAINS]:
            self._user_input[CONF_FILTER] = {
                ef.CONF_EXCLUDE_DOMAINS: list(DOMAIN_TO_YANDEX_TYPES.keys())
            }
        
        await self.async_step_selective()

    async def async_step_selective(self, user_input=None):
        """Step 4: Select entities to include/exclude."""

        reason = self._pre_step_check()
        if reason:
            self.async_abort(reason=reason)

        def show_form(error=None):
            return self.async_show_form(
                step_id="selective",
                data_schema=vol.Schema(self.entities_schema),
                errors={} if not error else {"base": error}
            )

        if not user_input or ef.CONF_EXCLUDE_ENTITIES not in user_input or ef.CONF_INCLUDE_ENTITIES not in user_input:
            return show_form()

        filter_config = {}
        for key in (ef.CONF_INCLUDE_ENTITIES, ef.CONF_EXCLUDE_ENTITIES):
            key_config = []

            val = user_input[key].replace(' ', '')
            if val:
                for entity_id in val.split(','):
                    if not valid_entity_id(entity_id):
                        return show_form("invalid_entity_id" if entity_id else "empty_entity_id")
                    key_config.append(entity_id)
                
                filter_config[key] = key_config

        if user_input[CONF_CUSTOMIZE_EXPOSURE] and not filter_config[ef.CONF_INCLUDE_ENTITIES]:
            return show_form("customization_unavailable_with_empty_includes")
        
        if len(filter_config.keys()) == 2:
            if any(x in filter_config[ef.CONF_INCLUDE_ENTITIES] for x in filter_config[ef.CONF_EXCLUDE_ENTITIES]):
                return show_form("conflicting_entity_includes")

        if filter_config:
            self._user_input[CONF_FILTER].update(filter_config)

        if user_input[CONF_CUSTOMIZE_EXPOSURE]:
            return await self.async_step_custom()
        else:
            return self._create_entry()

    async def async_step_custom(self, user_input=None):
        """Step 5: Customize per-entity exposure."""
        
        reason = self._pre_step_check()
        if reason:
            self.async_abort(reason=reason)

        if self._custom_entity_config:
            self._user_input[CONF_ENTITY_CONFIG][self._custom_entity_id] = \
                self._custom_entity_config

            self._custom_entity_config = None

        if user_input:
            if user_input[CONF_TYPE]:
                self._custom_entity_config[CONF_TYPE] = user_input[CONF_TYPE]
            
            if CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID in user_input:
                self._custom_entity_config[CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID] = \
                    user_input[CONF_TYPE]

            custom_properties = user_input.get(CONF_ENTITY_PROPERTIES, False)
            custom_toggles = user_input.get(CONF_ENTITY_TOGGLES, False)

            if custom_properties:
                if custom_toggles:
                    self._custom_entity_config[CONF_ENTITY_TOGGLES] = True
                return await self.async_step_custom_properties()
            elif custom_toggles:
                return await self.async_step_custom_toggles()

        if self._custom_entities_remaining is None:
            included_entities = self._user_input[CONF_FILTER][ef.CONF_INCLUDE_ENTITIES]
            self._custom_entities_remaining = included_entities.copy()

        while self._custom_entities_remaining:
            entity_id = self._custom_entities_remaining.pop()
            
            domain = entity_id.split('.')[0]
            schema = {}
            
            schema[vol.Optional(CONF_TYPE)] = vol.In(YANDEX_DEVICE_SUBTYPES)

            if domain == media_player.DOMAIN:
                schema[vol.Optional(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, default=False)] = bool
            
            #schema[vol.Optional(CONF_ENTITY_PROPERTIES, default=False)] = bool
            if domain not in (sensor.DOMAIN,):
                schema[vol.Optional(CONF_ENTITY_TOGGLES, default=False)] = bool

            self._custom_entity_id = entity_id
            self._custom_entity_config = {}

            return self.async_show_form(
                    step_id="custom",
                    data_schema=vol.Schema(schema),
                    description_placeholders={
                        "entity_id": entity_id,
                    },
                    errors={}
                )

        # Finish flow
        return self._create_entry()

    @property
    def available_properties(self):
        # @TODO: finish this
        pass

    async def async_step_custom_properties(self, user_input=None):
        # @TODO: finish this
        pass

    @property
    def available_toggles(self):
        if self._available_toggles is None:
            self._available_toggles = {
                vol.Optional(instance, default=''): str
                for instance in _ToggleCapability.get_child_instances()
            }
        return self._available_toggles

    async def async_step_custom_toggles(self, user_input=None):
        reason = self._pre_step_check()
        if reason:
            self.async_abort(reason=reason)

        def show_form(error=None):
            return self.async_show_form(
                step_id="custom_toggles",
                data_schema=vol.Schema(self.available_toggles),
                description_placeholders={
                    "entity_id": self._custom_entity_id,
                },
                errors={} if not error else {"base": error}
            )

        if not user_input:
            show_form()
        
        for _, override_entity_id in user_input.items():
            if not valid_entity_id(override_entity_id):
                return show_form("invalid_override_entity_id")
            parts = override_entity_id.split('.')
            domain = parts[0]
            if domain in (script.DOMAIN,):
                return show_form("invalid_entity_domain")
        
        self._custom_entity_config[CONF_ENTITY_TOGGLES] = user_input
        
        return await self.async_step_custom()

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
