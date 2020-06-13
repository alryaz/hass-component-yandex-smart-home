"""Config flow for the Yandex Smart Home component."""
__all__ = [
    'YandexSmartHomeFlowHandler'
]

import logging
from collections import OrderedDict
from typing import Any, Dict, Optional, List, Tuple, Union, Callable, Awaitable

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import (
    media_player,
    script
)
from homeassistant.config import YAML_CONFIG_FILE
from homeassistant.const import ATTR_FRIENDLY_NAME, CONF_ENTITY_ID
from homeassistant.core import valid_entity_id
from homeassistant.helpers import entityfilter as ef

from .const import (
    DOMAIN, CONF_FILTER, CONF_ENTITY_CONFIG,
    TYPE_OTHER, CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_TYPE,
    PREFIX_TYPES, CONF_ENTITY_PROPERTIES, CONF_ENTITY_TOGGLES, CONF_ATTRIBUTE)
from .core.helpers import get_child_instances, AnyInstanceType
from .core.type_mapper import get_supported_types, DOMAIN_TO_YANDEX_TYPES
from .functions.capability import CAPABILITIES, CAPABILITIES_TOGGLE
from .functions.prop import PROPERTIES

_LOGGER = logging.getLogger(__name__)

CONF_ADVANCED_CONFIGURATION = "advanced_configuration"
YANDEX_DEVICE_SUBTYPES = sorted(map(lambda x: x.replace(PREFIX_TYPES, ''), get_supported_types()))

DEFAULT_INCLUDE_ENTITIES = ''
DEFAULT_EXCLUDE_ENTITIES = ''
DEFAULT_CUSTOMIZE_EXPOSURE = False
DEFAULT_ADVANCED_ENABLE = False
DEFAULT_ADDITIONAL_ENABLE = False

PAGE_FIELD_MAX_COUNT = 5

AdditionalStepWrapperType = Callable[
    ['YandexSmartHomeFlowHandler', Optional[Dict[str, str]]],
    Awaitable[Dict[str, Any]]
]

ADDITIONAL_STEP_WRAPPERS: Dict[str, AdditionalStepWrapperType] = dict()
ADDITIONAL_STEP_PREFIX = 'custom_'


def custom_additional_step(key: str, source: List[AnyInstanceType], _type: Optional[str] = None):
    step_id = ADDITIONAL_STEP_PREFIX + key

    def wrapper_generator(func: Callable[['YandexSmartHomeFlowHandler', Dict[str, str]], Tuple[bool, Dict[str, Any]]]) \
            -> AdditionalStepWrapperType:

        async def wrapper(self: 'YandexSmartHomeFlowHandler', user_input: Optional[Dict[str, str]] = None) \
                -> Dict[str, Any]:

            _LOGGER.debug('async_step_%s %s [last_jndex=%s]' % (step_id, user_input, self._last_jndex))
            reason = self._check_before_step()
            if reason:
                return self.async_abort(reason=reason)

            if self._last_jndex is None:
                self._last_jndex = 0

            if self.custom_additional_schemas is None:
                self.custom_additional_schemas = dict()

            step_schemas = self.custom_additional_schemas.get(step_id)
            if step_schemas is None:
                step_schemas = self._generate_instance_schemas(source, _type)
                self.custom_additional_schemas[step_id] = step_schemas

            entity_id, friendly_name, placeholders, exposure_dict = self._get_exposure_attributes(
                i=self._last_jndex,
                p=len(step_schemas)
            )

            if user_input is None:
                _LOGGER.debug('[%s] Show form on missing input' % step_id)
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=step_schemas[self._last_jndex],
                    description_placeholders=placeholders
                )

            success, result_dict = func(self, user_input)

            if success:
                if result_dict is not None:
                    _LOGGER.debug('[%s] Merging result data: %s' % (step_id, result_dict))
                    self._merge_exposure_items(entity_id, {key: result_dict})
                else:
                    _LOGGER.debug('[%s] Not merging on no result' % step_id)
            else:
                _LOGGER.debug('[%s] Invalidated user input, errors: %s' % (step_id, result_dict))
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=step_schemas[self._last_jndex],
                    description_placeholders=placeholders,
                    errors=result_dict
                )

            return await self._run_additional_steps()

        ADDITIONAL_STEP_WRAPPERS[key] = wrapper

        return wrapper

    return wrapper_generator


class YandexSmartHomeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Yandex Smart Home."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def __getattribute__(self, item: str):
        if item.startswith('async_step_' + ADDITIONAL_STEP_PREFIX):
            # Find custom step
            key = item[11 + len(ADDITIONAL_STEP_PREFIX):]
            if key in ADDITIONAL_STEP_WRAPPERS:
                # noinspection PyUnresolvedReferences
                return ADDITIONAL_STEP_WRAPPERS[key].__get__(self, self.__class__)

        return super(YandexSmartHomeFlowHandler, self).__getattribute__(item)

    def __init__(self):
        """Initialize Yandex Smart Home config flow."""
        super().__init__()

        self._current_config: Optional[Dict[str, Any]] = None
        self._last_index: Optional[int] = None
        self._last_jndex: Optional[int] = None

        self.supported_domains = [
            domain
            for domain, yandex_type in DOMAIN_TO_YANDEX_TYPES.items()
            if yandex_type != TYPE_OTHER
        ]

        configuration_type_schema = OrderedDict()
        configuration_type_schema[vol.Optional(CONF_ADVANCED_CONFIGURATION, default=DEFAULT_ADVANCED_ENABLE)] = bool
        self.configuration_type_schema = vol.Schema(configuration_type_schema)

        self.supported_schemas = None
        self.unsupported_schemas = None
        self.entity_filter_schema = None
        self.custom_additional_schemas = None

    def _generate_custom_schemas(self):
        """Generate schemas for support and unsupported domains."""
        supported_schemas = []
        unsupported_schemas = []

        current_supported_schema = OrderedDict()
        current_unsupported_schema = OrderedDict()

        for domain, yandex_type in DOMAIN_TO_YANDEX_TYPES.items():
            if domain in self.supported_domains:
                if len(current_supported_schema) == PAGE_FIELD_MAX_COUNT:
                    supported_schemas.append(vol.Schema(current_supported_schema))
                    current_supported_schema = OrderedDict()

                current_supported_schema[vol.Optional(domain, default=True)] = bool

            else:
                if len(current_unsupported_schema) == PAGE_FIELD_MAX_COUNT:
                    unsupported_schemas.append(vol.Schema(current_unsupported_schema))
                    current_unsupported_schema = OrderedDict()

                current_unsupported_schema[vol.Optional(domain, default=False)] = bool

        if current_supported_schema:
            supported_schemas.append(vol.Schema(current_supported_schema))

        if current_unsupported_schema:
            unsupported_schemas.append(vol.Schema(current_unsupported_schema))

        self.supported_schemas = supported_schemas
        self.unsupported_schemas = unsupported_schemas

        entities_schema = OrderedDict()
        entities_schema[vol.Optional(ef.CONF_INCLUDE_ENTITIES, default=DEFAULT_INCLUDE_ENTITIES)] = str
        entities_schema[vol.Optional(ef.CONF_EXCLUDE_ENTITIES, default=DEFAULT_EXCLUDE_ENTITIES)] = str
        entities_schema[vol.Optional(CONF_ENTITY_CONFIG, default=DEFAULT_CUSTOMIZE_EXPOSURE)] = bool
        self.entity_filter_schema = vol.Schema(entities_schema)

    @staticmethod
    def _generate_instance_schemas(source: List[AnyInstanceType], _type: Optional[str] = None) -> List[vol.Schema]:
        """
        Generate list of schemas for instance-bound classes (capabilities, properties)
        :param source: List of property / capability classes
        :param _type: (optional) Filter by specific type
        :return: Schema list
        """
        custom_schemas = []
        current_schema = OrderedDict()

        for instance in get_child_instances(source, _type):
            if len(current_schema) == PAGE_FIELD_MAX_COUNT:
                custom_schemas.append(vol.Schema(current_schema))
                current_schema = OrderedDict()

            current_schema[vol.Optional(instance)] = str

        custom_schemas.append(vol.Schema(current_schema))

        return custom_schemas

    def _check_before_step(self):
        """Perform common checks before running steps."""
        if self._async_current_entries():
            return "single_instance_allowed"

    def _include_domains_from_input(self, user_input: Dict[str, bool]) -> List[str]:
        """
        Include domains from `supported` and `unsupported` steps.
        :param user_input: Dictionary of `<domain>` => `<choice>`
        :return: List of all included domains
        """
        included_domains = [
            domain
            for domain, choice in user_input.items()
            if choice is True
        ]

        if included_domains:
            if ef.CONF_INCLUDE_DOMAINS in self._current_config[CONF_FILTER]:
                self._current_config[CONF_FILTER][ef.CONF_INCLUDE_DOMAINS].extend(included_domains)
            else:
                self._current_config[CONF_FILTER][ef.CONF_INCLUDE_DOMAINS] = included_domains

        return included_domains

    def _create_entry(self) -> Dict[str, Any]:
        """Finish config flow and create entry from current configuration."""
        _LOGGER.debug('Create config: %s' % self._current_config)

        # Clear empty keys
        delete_keys = [k for k, v in self._current_config.items() if not v]
        for key in delete_keys:
            del self._current_config[key]

        return self.async_create_entry(
            title=f'Default',
            data=self._current_config,
        )

    def _get_exposure_attributes(self, entity_id: Optional[str] = None, i: Optional[int] = None,
                                 p: Optional[int] = None, e_i: Optional[int] = None) \
            -> Tuple[str, str, Dict[str, Union[str, int]], Optional[Dict[str, Any]]]:
        if i is None:
            i = self._last_index

        if e_i is None:
            e_i = self._last_index

        if p is None:
            p = len(self._included_entities)

        if entity_id is None:
            entity_id = self._included_entities[e_i]

        state = self.hass.states.get(entity_id)

        friendly_name = "?"
        if state:
            friendly_name = state.attributes.get(ATTR_FRIENDLY_NAME, friendly_name)

        placeholders = {"entity_id": entity_id, "friendly_name": friendly_name, "page": i + 1, "pages": p}

        exposure_dict = None
        if CONF_ENTITY_CONFIG in self._current_config:
            exposure_dict = self._current_config[CONF_ENTITY_CONFIG].get(entity_id)

        return entity_id, friendly_name, placeholders, exposure_dict

    @property
    def _included_entities(self) -> List[str]:
        """
        Shortcut to return included entities list.
        :return: List[<entity_id>]
        """
        return self._current_config[CONF_FILTER][ef.CONF_INCLUDE_ENTITIES]

    def _merge_exposure_items(self, entity_id: str, items: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge data to entity's exposure configuration.
        Create exposure dictionary first should it not exist.
        :param entity_id: Entity ID to perform merge for
        :param items: Exposure configuration
        :return: Merged entity exposure configuration
        """
        customize_exposure = self._current_config.setdefault(CONF_ENTITY_CONFIG, dict())

        if entity_id in customize_exposure:
            customize_exposure[entity_id].update(items)
        else:
            customize_exposure[entity_id] = {**items}

        return customize_exposure

    # GUI steps
    async def async_step_user(self, user_input: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Step 2: Handle a flow initialized by the user."""
        _LOGGER.debug('async_step_user %s' % user_input)

        reason = self._check_before_step()
        if reason:
            return self.async_abort(reason=reason)

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=self.configuration_type_schema,
                description_placeholders={
                    'domains': '`' + '`, `'.join(self.supported_domains) + '`'
                }
            )

        if user_input.get(CONF_ADVANCED_CONFIGURATION):
            return await self.async_step_supported()

        self._current_config = {
            CONF_FILTER: {
                ef.CONF_INCLUDE_DOMAINS: self.supported_domains
            }
        }
        return self._create_entry()

    async def async_step_supported(self, user_input: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Step 2: Initiate special configuration."""
        _LOGGER.debug('async_step_supported %s' % user_input)

        reason = self._check_before_step()
        if reason:
            return self.async_abort(reason=reason)

        if self.supported_schemas is None:
            self._generate_custom_schemas()

        if user_input is None:
            # Show form with a list of supported domains
            if self._last_index is None:
                self._last_index = 0

            _LOGGER.debug('Showing page %d of %d from supported schemas'
                          % (self._last_index + 1, len(self.supported_schemas)))

            return self.async_show_form(
                step_id="supported",
                data_schema=self.supported_schemas[self._last_index],
                errors={},
                description_placeholders={
                    "page": self._last_index + 1,
                    "pages": len(self.supported_schemas)
                }
            )

        if self._current_config is None:
            self._current_config = {
                CONF_FILTER: {},
                CONF_ENTITY_CONFIG: {},
            }

        self._include_domains_from_input(user_input)

        self._last_index += 1
        if self._last_index < len(self.supported_schemas):
            return await self.async_step_supported()

        self._last_index = None

        if self.unsupported_schemas:
            return await self.async_step_unsupported()

        return await self.async_step_selective()

    async def async_step_unsupported(self, user_input: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Step 3: Enable unsupported domains on demand."""
        _LOGGER.debug('async_step_unsupported %s' % user_input)

        reason = self._check_before_step()
        if reason:
            return self.async_abort(reason=reason)

        if user_input is None:
            # Show form with a list of unsupported domains
            if self._last_index is None:
                self._last_index = 0

            return self.async_show_form(
                step_id="unsupported",
                data_schema=self.unsupported_schemas[self._last_index],
                errors={},
                description_placeholders={
                    "page": self._last_index + 1,
                    "pages": len(self.unsupported_schemas),
                }
            )

        self._include_domains_from_input(user_input)

        self._last_index += 1
        if self._last_index < len(self.unsupported_schemas):
            return await self.async_step_unsupported()

        self._last_index = None

        return await self.async_step_selective()

    async def async_step_selective(self, user_input: Optional[Dict[str, Union[str, bool]]] = None) -> Dict[str, Any]:
        """Step 4: Select entities to include/exclude."""
        _LOGGER.debug('async_step_selective %s' % user_input)

        reason = self._check_before_step()
        if reason:
            return self.async_abort(reason=reason)

        include_exclude_keys = (ef.CONF_INCLUDE_ENTITIES, ef.CONF_EXCLUDE_ENTITIES)

        if not user_input or any(a not in user_input for a in include_exclude_keys):
            return self.async_show_form(
                step_id="selective",
                data_schema=self.entity_filter_schema
            )

        errors, placeholders = dict(), dict()
        filter_config = {}
        for key in include_exclude_keys:
            # Iterate over lists of filtered entity IDs
            filter_input = user_input[key].replace(' ', '')
            if filter_input:
                key_config = []

                for entity_id in filter_input.split(','):
                    # Iterate over extracted entity IDs
                    if not entity_id:
                        errors[key] = "empty_entity_id"
                        break

                    elif not valid_entity_id(entity_id):
                        errors[key] = "invalid_entity_id"
                        placeholders['invalid_entity_id'] = entity_id
                        break

                    key_config.append(entity_id)

                filter_config[key] = key_config

        if user_input[CONF_ENTITY_CONFIG] and not filter_config.get(ef.CONF_INCLUDE_ENTITIES):
            # Fail customization on empty includes list
            errors[CONF_ENTITY_CONFIG] = "customization_unavailable_with_empty_includes"

        if all(a in filter_config for a in include_exclude_keys):
            # Confirm both filter poles are configured
            if set(filter_config[ef.CONF_INCLUDE_ENTITIES]).intersection(filter_config[ef.CONF_EXCLUDE_ENTITIES]):
                # Fail setup on intersecting entity include/exclude lists
                errors['base'] = "conflicting_entity_includes"

        if errors:
            # There are errors, show them
            return self.async_show_form(
                step_id="selective",
                data_schema=self.entity_filter_schema,
                errors=errors,
                data_placeholders=placeholders
            )

        if filter_config:
            # Update previous filter configuration
            if CONF_FILTER in self._current_config:
                self._current_config[CONF_FILTER].update(filter_config)
            else:
                self._current_config[CONF_FILTER] = filter_config

        elif CONF_FILTER not in self._current_config:
            # Check if filter returns no entities at all
            return self.async_show_form(
                step_id="selective",
                data_schema=self.entity_filter_schema,
                errors={"base": "filter_without_entities"}
            )

        if user_input[CONF_ENTITY_CONFIG]:
            return await self.async_step_custom()

        return self._create_entry()

    async def async_step_custom(self, user_input: Optional[Dict[str, Union[str, bool]]] = None) -> Dict[str, Any]:
        """Step 5: Customize per-entity exposure."""
        _LOGGER.debug('async_step_custom %s [last_index=%s]' % (user_input, self._last_index))

        reason = self._check_before_step()
        if reason:
            return self.async_abort(reason=reason)

        if self._last_index is None:
            self._last_index = 0
        elif user_input is None:
            self._last_index += 1

        if self._last_index < len(self._included_entities):
            entity_id, friendly_name, placeholders, _ = self._get_exposure_attributes()

            if user_input is None:
                domain = entity_id.split('.')[0]
                schema = OrderedDict()
                schema[vol.Optional(CONF_TYPE)] = vol.In(YANDEX_DEVICE_SUBTYPES)

                # For media players, enable `channel_set_via_media_content_id`
                if domain == media_player.DOMAIN:
                    schema[vol.Optional(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, default=False)] = bool

                # Add additional steps
                for key, step in ADDITIONAL_STEP_WRAPPERS.items():
                    schema[vol.Optional(key, default=DEFAULT_ADDITIONAL_ENABLE)] = bool

                return self.async_show_form(
                    step_id="custom",
                    data_schema=vol.Schema(schema),
                    description_placeholders=placeholders
                )

            if user_input:
                self._merge_exposure_items(entity_id, user_input)
                return await self._run_additional_steps()

        # Finish flow
        return self._create_entry()

    async def _run_additional_steps(self):
        entity_id = self._included_entities[self._last_index]
        exposure_dict = self._current_config[CONF_ENTITY_CONFIG].get(entity_id, {})

        _LOGGER.debug('Running additional steps with exposure dict: %s' % exposure_dict)

        for key, wrapper in ADDITIONAL_STEP_WRAPPERS.items():
            enabled = exposure_dict.get(key)

            if enabled is not None:
                if isinstance(enabled, bool):
                    _LOGGER.debug('Clearing key: %s' % key)
                    del exposure_dict[key]

                    if enabled is True:
                        _LOGGER.debug('Awaiting additional step: %s' % key)
                        return await wrapper(self, None)

                elif not enabled:
                    _LOGGER.debug('Key %s contains empty config' % key)
                    del exposure_dict[key]

        if not exposure_dict:
            del self._current_config[CONF_ENTITY_CONFIG][entity_id]

        return self._create_entry()

    @custom_additional_step(CONF_ENTITY_TOGGLES, CAPABILITIES, CAPABILITIES_TOGGLE)
    def custom_toggles_processor(self, user_input: Dict[str, str]):
        """This is a processor for custom_toggles"""
        errors: Dict[str, str] = dict()
        for instance, override_entity_id in user_input.items():
            if not valid_entity_id(override_entity_id):
                errors[instance] = "invalid_entity_id"
                continue

            parts = override_entity_id.split('.')
            if parts[0] in (script.DOMAIN,):
                errors[instance] = "invalid_domain"

        return not errors, errors or user_input

    @custom_additional_step(CONF_ENTITY_PROPERTIES, PROPERTIES)
    def custom_properties_processor(self, user_input: Dict[str, str]):
        """This is a processor for custom_properties"""
        entity_properties = dict()
        errors = dict()
        for instance, value in user_input.items():
            entity_property = dict()
            parts = value.split('.')
            parts_count = len(parts)

            if parts_count > 1:
                entity_id = '.'.join(parts[:2])
                if not valid_entity_id:
                    errors[instance] = "invalid_entity_id"
                    continue

                entity_property[CONF_ENTITY_ID] = entity_id
                if 2 < len(parts) < 4:
                    entity_property[CONF_ATTRIBUTE] = '.'.join(parts[2])
                else:
                    errors[instance] = "invalid_entity_attribute"
                    continue

            else:
                entity_property[CONF_ATTRIBUTE] = parts[0]

            if entity_property:
                entity_properties[instance] = entity_property

        return not errors, errors or entity_properties

    # Import step
    async def async_step_import(self, _) -> Dict[str, Any]:
        """Import a config entry from configuration.yaml."""
        if self._async_current_entries():
            _LOGGER.warning("Only one configuration of Yandex Smart Home is allowed.")
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title=YAML_CONFIG_FILE,
            data={},
            description='Configuration imported from YAML'
        )
