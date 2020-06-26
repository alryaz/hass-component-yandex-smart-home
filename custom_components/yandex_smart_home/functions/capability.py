"""Implement the Yandex Smart Home capabilities."""
import logging
from typing import Any, Optional, Dict, TYPE_CHECKING, Tuple, Type, List, Union

from homeassistant.components import (
    automation,
    camera,
    climate,
    cover,
    group,
    fan,
    input_boolean,
    media_player,
    light,
    scene,
    script,
    switch,
    vacuum,
    water_heater,
    lock,
)
from homeassistant.components.water_heater import (
    STATE_ELECTRIC, SERVICE_SET_OPERATION_MODE
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_MUTE,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    STATE_OFF,
    STATE_ON, CONF_ENTITY_ID,
    CONF_MAXIMUM, CONF_MINIMUM
)
from homeassistant.core import DOMAIN as HA_DOMAIN, State
from homeassistant.helpers.script import Script
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import color as color_util

from custom_components.yandex_smart_home.const import (
    ERR_INVALID_VALUE,
    ERR_NOT_SUPPORTED_IN_CURRENT_MODE, CONF_PROGRAMS,
    CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID, CONF_RELATIVE_VOLUME_ONLY,
    CONF_INPUT_SOURCES, CONF_ENTITY_TOGGLES,
    CONF_SCRIPT_CHANNEL_UP, CONF_SCRIPT_CHANNEL_DOWN, CONF_ENTITY_MODES, CONF_MAPPING, ERR_INTERNAL_ERROR,
    CONF_SET_SCRIPT, CONF_PRECISION, CONF_MULTIPLIER, CONF_ENTITY_RANGES, MODES_NUMERIC, ATTR_VALUE)
from custom_components.yandex_smart_home.core.error import SmartHomeError, DefaultNotImplemented, \
    OverrideNotImplemented

if TYPE_CHECKING:
    from custom_components.yandex_smart_home.core.helpers import RequestData

_LOGGER = logging.getLogger(__name__)

PREFIX_CAPABILITIES = 'devices.capabilities.'
CAPABILITIES_ON_OFF = PREFIX_CAPABILITIES + 'on_off'
CAPABILITIES_TOGGLE = PREFIX_CAPABILITIES + 'toggle'
CAPABILITIES_RANGE = PREFIX_CAPABILITIES + 'range'
CAPABILITIES_MODE = PREFIX_CAPABILITIES + 'mode'
CAPABILITIES_COLOR_SETTING = PREFIX_CAPABILITIES + 'color_setting'

CAPABILITIES: List[Type['_Capability']] = []


def register_capability(capability):
    """Decorate a function to register a capability."""
    CAPABILITIES.append(capability)
    return capability


class _Capability(object):
    """Represents a Capability."""

    type = NotImplemented
    instance = NotImplemented
    retrievable = True

    def __init__(self, hass: HomeAssistantType, state: State, entity_config: Dict):
        """Initialize a trait for a state."""
        self.hass = hass
        self.state = state
        self.entity_config = entity_config

        self.use_override = self.has_override(state.domain, entity_config, state.attributes)

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Check whether current entity is supported."""
        return False

    @classmethod
    def has_override(cls, domain: str, entity_config: Dict, attributes: Dict) -> bool:
        """Return whether current capability instance has associated overrides.

        Capabilities can implement this method as well as the next two
        to provide ways to implement configuration-bound overrides.
        """
        return False

    def description(self) -> Dict:
        """Return description for a devices request."""
        response = {
            'type': self.type,
            'retrievable': self.retrievable,
        }
        parameters = self.parameters()
        if parameters is not None:
            response['parameters'] = parameters

        return response

    def get_state(self) -> Dict:
        """Return the state of this capability for this entity."""
        return {
            'type': self.type,
            'state': {
                'instance': self.instance,
                'value': self.get_value(),
            }
        }

    def parameters(self) -> Dict:
        """Return parameters for a devices request."""
        if self.use_override:
            return self.parameters_override()
        return self.parameters_default()

    def parameters_default(self) -> Dict[str, Any]:
        raise DefaultNotImplemented(self.__class__)

    def parameters_override(self) -> Dict[str, Any]:
        raise OverrideNotImplemented(self.__class__)

    def get_value(self) -> Any:
        """Return the state value of this capability for this entity."""
        if self.use_override:
            return self.get_value_override()
        return self.get_value_default()

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity using default mechanism."""
        raise DefaultNotImplemented(self.__class__)

    def get_value_override(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity using override."""
        raise OverrideNotImplemented(self.__class__)

    async def set_state(self, data: 'RequestData', state: Dict) -> None:
        """Set device state."""
        if self.use_override:
            return await self.set_state_override(data, state)
        return await self.set_state_default(data, state)

    async def set_state_default(self, data: 'RequestData', state: Dict) -> None:
        """Set device state."""
        raise DefaultNotImplemented(self.__class__)

    async def set_state_override(self, data: 'RequestData', state: Dict) -> None:
        """Set device state using override."""
        raise OverrideNotImplemented(self.__class__)


@register_capability
class OnOffCapability(_Capability):
    """On_off to offer basic on and off functionality.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/on_off-docpage/
    """

    type = CAPABILITIES_ON_OFF
    instance = 'on'

    water_heater_operations = {
        STATE_ON: [STATE_ON, 'On', 'ON', STATE_ELECTRIC],
        STATE_OFF: [STATE_OFF, 'Off', 'OFF'],
    }

    def __init__(self, hass, state, config):
        super().__init__(hass, state, config)
        self.retrievable = state.domain not in (scene.DOMAIN, script.DOMAIN)

    @classmethod
    def get_water_heater_operation(cls, required_mode, operations_list):
        for operation in cls.water_heater_operations[required_mode]:
            if operation in operations_list:
                return operation
        return None

    @classmethod
    def issue_state_retrieval(cls, entity_state: State) -> bool:
        """Return the state value of this capability for given entity."""
        entity_domain = entity_state.domain
        current_state = entity_state.state

        if entity_domain == cover.DOMAIN:
            return current_state == cover.STATE_OPEN

        elif entity_domain == vacuum.DOMAIN:
            return current_state == STATE_ON or current_state == \
                   vacuum.STATE_CLEANING

        elif entity_domain == climate.DOMAIN:
            return current_state != climate.HVAC_MODE_OFF

        elif entity_domain == lock.DOMAIN:
            return current_state == lock.STATE_UNLOCKED

        elif entity_domain == water_heater.DOMAIN:
            operation_mode = entity_state.attributes.get(water_heater.ATTR_OPERATION_MODE)
            operation_list = entity_state.attributes.get(water_heater.ATTR_OPERATION_LIST)
            return operation_mode != cls.get_water_heater_operation(STATE_OFF, operation_list)

        return current_state != STATE_OFF

    @classmethod
    async def issue_state_command(cls, hass: HomeAssistantType, entity_state: State, data: 'RequestData', state: Dict):
        """Set state for given entity."""
        new_state = state['value']
        if type(new_state) is not bool:
            raise SmartHomeError(ERR_INVALID_VALUE, "Value is not boolean")

        entity_domain = entity_state.domain
        entity_id = entity_state.entity_id

        service_domain = entity_domain
        service_data = {
            ATTR_ENTITY_ID: entity_id,
        }
        if entity_domain == group.DOMAIN:
            service_domain = HA_DOMAIN
            service = SERVICE_TURN_ON if new_state else SERVICE_TURN_OFF

        elif entity_domain == cover.DOMAIN:
            service = SERVICE_OPEN_COVER if new_state else \
                SERVICE_CLOSE_COVER

        elif entity_domain == vacuum.DOMAIN:
            features = entity_state.attributes.get(ATTR_SUPPORTED_FEATURES)
            if new_state:
                if features & vacuum.SUPPORT_START:
                    service = vacuum.SERVICE_START
                else:
                    service = SERVICE_TURN_ON
            else:
                if features & vacuum.SUPPORT_RETURN_HOME:
                    service = vacuum.SERVICE_RETURN_TO_BASE
                elif features & vacuum.SUPPORT_STOP:
                    service = vacuum.SERVICE_STOP
                else:
                    service = SERVICE_TURN_OFF

        elif entity_domain == scene.DOMAIN or entity_domain == script.DOMAIN:
            if new_state is False:
                _LOGGER.warning(("An 'off' command was issued via Yandex to %s. "
                                 "Please, check your configuration.") % entity_id)
                return
            service = SERVICE_TURN_ON

        elif entity_domain == lock.DOMAIN:
            service = SERVICE_UNLOCK if new_state else \
                SERVICE_LOCK

        elif entity_domain == water_heater.DOMAIN:
            operation_list = entity_state.attributes.get(water_heater.ATTR_OPERATION_LIST)
            service = SERVICE_SET_OPERATION_MODE
            if new_state:
                service_data[water_heater.ATTR_OPERATION_MODE] = \
                    cls.get_water_heater_operation(STATE_ON, operation_list)
            else:
                service_data[water_heater.ATTR_OPERATION_MODE] = \
                    cls.get_water_heater_operation(STATE_OFF, operation_list)
        else:
            service = SERVICE_TURN_ON if new_state else SERVICE_TURN_OFF

        await hass.services.async_call(
            service_domain,
            service,
            service_data,
            blocking=(entity_domain != script.DOMAIN),
            context=data.context
        )

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        if domain == media_player.DOMAIN:
            return features & media_player.SUPPORT_TURN_ON and features & media_player.SUPPORT_TURN_OFF

        if domain == vacuum.DOMAIN:
            return (features & vacuum.SUPPORT_START and (
                    features & vacuum.SUPPORT_RETURN_HOME or features & vacuum.SUPPORT_STOP)) or (
                               features & vacuum.SUPPORT_TURN_ON and features & vacuum.SUPPORT_TURN_OFF)

        if domain == water_heater.DOMAIN and features & water_heater.SUPPORT_OPERATION_MODE:
            operation_list = attributes.get(water_heater.ATTR_OPERATION_LIST)
            if cls.get_water_heater_operation(STATE_ON, operation_list) is None:
                return False
            if cls.get_water_heater_operation(STATE_OFF, operation_list) is None:
                return False
            return True

        return domain in (
            automation.DOMAIN,
            camera.DOMAIN,
            cover.DOMAIN,
            group.DOMAIN,
            input_boolean.DOMAIN,
            switch.DOMAIN,
            fan.DOMAIN,
            light.DOMAIN,
            climate.DOMAIN,
            scene.DOMAIN,
            script.DOMAIN,
            lock.DOMAIN,
        )

    def parameters(self):
        """Return parameters for a devices request."""
        return None

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        return self.issue_state_retrieval(self.state)

    async def set_state_default(self, data: 'RequestData', state: Dict):
        """Set state for this entity."""
        await self.issue_state_command(self.hass, self.state, data, state)


class _ToggleCapability(_Capability):
    """Base toggle functionality.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-docpage/
    """
    type = CAPABILITIES_TOGGLE

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return False

    @classmethod
    def has_override(cls, domain: str, entity_config: Dict, attributes: Dict) -> bool:
        """Determine whether toggle capability has an override."""
        return bool(cls.get_override_entity_id(entity_config))

    def parameters(self):
        """Return parameters for a devices request."""
        return {
            'instance': self.instance
        }

    @classmethod
    def get_override_entity_id(cls, entity_config: Dict) -> Optional[str]:
        """Return override entity ID for toggles."""
        entity_toggles = entity_config.get(CONF_ENTITY_TOGGLES)
        if entity_toggles:
            return entity_toggles.get(cls.instance)

    @classmethod
    def get_override_entity_state(cls, hass: HomeAssistantType, entity_config: Dict) -> Optional[State]:
        """Get state of overriding entity."""
        entity_id = cls.get_override_entity_id(entity_config)
        if entity_id:
            return hass.states.get(entity_id)

    def get_value_override(self) -> Optional[Union[str, float, int]]:
        """Return override value."""
        override_entity_state = self.get_override_entity_state(self.hass, self.entity_config)
        return OnOffCapability.issue_state_retrieval(override_entity_state)

    async def set_state_override(self, data: 'RequestData', state: Dict):
        override_entity_state = self.get_override_entity_state(self.hass, self.entity_config)
        await OnOffCapability.issue_state_command(self.hass, override_entity_state, data, state)


@register_capability
class ControlsLockedCapability(_ToggleCapability):
    """Controls locking functionality."""

    instance = "controls_locked"


@register_capability
class BacklightCapability(_ToggleCapability):
    """Backlight functionality"""

    instance = "backlight"


@register_capability
class IonizationCapability(_ToggleCapability):
    """Ionization functionality."""

    instance = "ionization"


@register_capability
class KeepWarmCapability(_ToggleCapability):
    """Keep warm capability."""

    instance = "keep_warm"


@register_capability
class MuteCapability(_ToggleCapability):
    """Mute and unmute functionality."""

    instance = "mute"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        return domain == media_player.DOMAIN and features & media_player.SUPPORT_VOLUME_MUTE

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        muted = self.state.attributes.get(media_player.ATTR_MEDIA_VOLUME_MUTED)

        return bool(muted)

    async def set_state(self, data: 'RequestData', state: Dict):
        """Set device state."""
        if type(state['value']) is not bool:
            raise SmartHomeError(ERR_INVALID_VALUE, "Value is not boolean")

        muted = self.state.attributes.get(media_player.ATTR_MEDIA_VOLUME_MUTED)
        if muted is None:
            raise SmartHomeError(ERR_NOT_SUPPORTED_IN_CURRENT_MODE,
                                 "Device probably turned off")

        await self.hass.services.async_call(
            self.state.domain,
            SERVICE_VOLUME_MUTE, {
                ATTR_ENTITY_ID: self.state.entity_id,
                media_player.ATTR_MEDIA_VOLUME_MUTED: state['value']
            }, blocking=True, context=data.context)


@register_capability
class OscillationCapability(_ToggleCapability):
    """Oscillation capability"""

    instance = "oscillation"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return domain == fan.DOMAIN and \
            features & fan.SUPPORT_OSCILLATE

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state of oscillation for this entity."""
        return bool(self.state.attributes.get(fan.ATTR_OSCILLATING))

    async def set_state(self, data: 'RequestData', state: dict):
        if not isinstance(state['value'], bool):
            raise SmartHomeError(ERR_INVALID_VALUE, "Value is not boolean")

        await self.hass.services.async_call(
            fan.DOMAIN,
            fan.SERVICE_OSCILLATE, {
                ATTR_ENTITY_ID: self.state.entity_id,
                fan.ATTR_OSCILLATING: state['value']
            }, blocking=True, context=data.context)


@register_capability
class PauseCapability(_ToggleCapability):
    """Pause and unpause functionality."""

    instance = "pause"

    def __init__(self, hass: HomeAssistantType, state: State, entity_config: dict):
        super().__init__(hass, state, entity_config)
        self.retrievable = state.domain == media_player.DOMAIN or state.domain == vacuum.DOMAIN and (
                state.attributes.get(ATTR_SUPPORTED_FEATURES, 0) & vacuum.SUPPORT_STATE
        )

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        if domain == media_player.DOMAIN:
            return features & media_player.SUPPORT_PLAY and \
                features & media_player.SUPPORT_PAUSE
        elif domain == vacuum.DOMAIN:
            return features & vacuum.SUPPORT_PAUSE
        return False

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        return self.state.state != media_player.STATE_PLAYING

    async def set_state(self, data: 'RequestData', state: Dict):
        """Set device state."""
        if type(state['value']) is not bool:
            raise SmartHomeError(ERR_INVALID_VALUE, "Value is not boolean")

        domain = self.state.domain
        new_state = state['value']
        service = ''
        service_data = {
            ATTR_ENTITY_ID: self.state.entity_id,
        }

        if domain == media_player.DOMAIN:
            service = media_player.SERVICE_MEDIA_PAUSE if new_state else \
                media_player.SERVICE_MEDIA_PLAY

        elif domain == vacuum.DOMAIN:
            service = vacuum.SERVICE_PAUSE if new_state else \
                vacuum.SERVICE_START

        await self.hass.services.async_call(
            domain,
            service,
            service_data,
            blocking=True,
            context=data.context
        )


class _ModeCapability(_Capability):
    """Base class of capabilities with mode functionality like thermostat mode
    or fan speed.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-docpage/
    """

    type = CAPABILITIES_MODE
    internal_modes: Tuple[str] = NotImplemented

    def __init__(self, hass: HomeAssistantType, state: State, entity_config: Dict):
        super().__init__(hass, state, entity_config)

        self.set_script = Script(
            hass,
            self.get_override_config(entity_config)[CONF_SET_SCRIPT]
        ) if self.use_override else None

    @classmethod
    def has_override(cls, domain: str, entity_config: Dict, attributes: Dict) -> bool:
        """Determine whether mode capability has an override."""
        return bool(cls.get_override_config(entity_config))

    @classmethod
    def get_override_config(cls, entity_config: Dict) -> Optional[Dict[str, Any]]:
        """Return override entity ID for modes."""
        modes_config = entity_config.get(CONF_ENTITY_MODES)
        if modes_config:
            return modes_config.get(cls.instance)

    def parameters_override(self) -> Dict[str, Any]:
        override_config = self.get_override_config(self.entity_config)

        return {
            "instance": self.instance,
            "modes": [
                {"value": v}
                for v in (override_config[CONF_MAPPING].keys() if CONF_MAPPING in override_config
                          else self.internal_modes)
            ]
        }

    def get_value_override(self) -> Optional[Union[str, float, int]]:
        override_config = self.get_override_config(self.entity_config)

        override_entity_state = self.hass.states.get(override_config[CONF_ENTITY_ID])
        if override_entity_state:
            if CONF_MAPPING in override_config:
                for yandex_mode, states in override_config[CONF_MAPPING]:
                    if override_entity_state.state in states:
                        return yandex_mode

            elif override_entity_state.state in self.internal_modes:
                return override_entity_state.state

            raise SmartHomeError(
                ERR_INTERNAL_ERROR,
                msg='Mapping for state "%s" unavailable for entity "%s"'
                    % (override_entity_state.state, override_entity_state.entity_id)
            )

        return self.internal_modes[0]

    async def set_state_override(self, data: 'RequestData', state: Dict):
        override_config = self.get_override_config(self.entity_config)
        value = state['value']

        if CONF_MAPPING in override_config:
            if value not in override_config:
                raise SmartHomeError(ERR_INVALID_VALUE, msg="Unsupported mode")
            value = override_config[value][0]

        await self.set_script.async_run({
            ATTR_VALUE: value,
            ATTR_ENTITY_ID: override_config[CONF_ENTITY_ID]
        }, context=data.context)


class _NumericModeCapability(_ModeCapability):
    internal_modes = MODES_NUMERIC
    custom_numeric_mode_source = NotImplemented

    attr_list: Optional[str] = None
    attr_value: Optional[str] = None
    set_service: Optional[str] = None

    @classmethod
    def _numeric_mode_supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Check whether numeric mode is supported"""
        raise NotImplementedError

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return entity_config.get(cls.custom_numeric_mode_source) is not False \
               and cls._numeric_mode_supported(domain, features, entity_config, attributes)

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        program = self.state.attributes.get(self.attr_value)
        custom_numeric_modes = self.entity_config.get(self.custom_numeric_mode_source)

        if custom_numeric_modes is True:
            program_list = self.state.attributes.get(self.attr_list, [])
            iterator = zip(self.internal_modes, program_list)

        else:
            iterator = custom_numeric_modes.items()

        for yandex_program, local_program in iterator:
            if local_program == program:
                return yandex_program

        return self.internal_modes[0]

    def parameters_default(self) -> Dict[str, Any]:
        custom_numeric_modes = self.entity_config.get(self.custom_numeric_mode_source)

        if custom_numeric_modes is True:
            program_list = self.state.attributes.get(self.attr_list, [])
            modes = [
                {"value": self.internal_modes[i]}
                for i in range(0, min(len(program_list), 10))
            ]

        else:
            modes = [
                {"value": v}
                for v in custom_numeric_modes.keys()
            ]

        return {
            "instance": self.instance,
            "modes": modes,
        }

    async def set_state_default(self, data: 'RequestData', state: Dict[str, Any]):
        new_mode = state["value"]
        custom_programs = self.entity_config.get(self.custom_numeric_mode_source)

        if custom_programs is None:
            program_list = self.state.attributes.get(self.attr_list, [])
            iterator = zip(self.internal_modes, program_list)

        else:
            iterator = custom_programs.items()

        for yandex_mode, local_mode in iterator:
            if yandex_mode == new_mode:
                return await self.hass.services.async_call(
                    self.state.domain,
                    self.set_service, {
                        ATTR_ENTITY_ID: self.state.entity_id,
                        self.attr_value: local_mode,
                    }, blocking=True, context=data.context)

        raise SmartHomeError(ERR_INVALID_VALUE, "Unacceptable value")


@register_capability
class ProgramCapability(_NumericModeCapability):
    """Program functionality."""

    instance = "program"
    custom_numeric_mode_source = CONF_PROGRAMS

    program_attributes = {
        (climate.DOMAIN, climate.SUPPORT_PRESET_MODE): (
            climate.ATTR_PRESET_MODES,
            climate.ATTR_PRESET_MODE,
            climate.SERVICE_SET_PRESET_MODE,
        ),
        (light.DOMAIN, light.SUPPORT_EFFECT): (
            light.ATTR_EFFECT_LIST,
            light.ATTR_EFFECT,
            light.SERVICE_TURN_ON,
        ),
    }

    @classmethod
    def _numeric_mode_supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return bool(cls._get_program_attributes(domain, features))

    @classmethod
    def _get_program_attributes(cls, domain: str, features: int):
        for (supp_domain, feature), attributes in cls.program_attributes.items():
            if domain == supp_domain and features & feature:
                return attributes
        return None

    def __init__(self, hass: HomeAssistantType, state: State, entity_config):
        super().__init__(hass, state, entity_config)

        attributes = self._get_program_attributes(
            state.domain,
            state.attributes.get(ATTR_SUPPORTED_FEATURES)
        )

        if attributes:
            self.attr_list = attributes[0]
            self.attr_value = attributes[1]
            self.set_service = attributes[2]


@register_capability
class InputSourceCapability(_NumericModeCapability):
    """Input Source functionality"""

    instance = "input_source"
    custom_numeric_mode_source = CONF_INPUT_SOURCES

    attr_list = media_player.ATTR_INPUT_SOURCE_LIST
    attr_value = media_player.ATTR_INPUT_SOURCE
    set_service = media_player.SERVICE_SELECT_SOURCE

    @classmethod
    def _numeric_mode_supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        if domain == media_player.DOMAIN and features & media_player.SUPPORT_SELECT_SOURCE:
            return entity_config.get(CONF_INPUT_SOURCES) is not True or \
                   attributes.get(media_player.ATTR_INPUT_SOURCE_LIST) is None

        return False


@register_capability
class ThermostatCapability(_ModeCapability):
    """Thermostat functionality"""

    instance = 'thermostat'
    internal_modes = ('auto', 'cool', 'dry', 'fan_only', 'heat', 'preheat')

    climate_map = {
        climate.const.HVAC_MODE_AUTO: internal_modes[0],
        climate.const.HVAC_MODE_COOL: internal_modes[1],
        climate.const.HVAC_MODE_DRY: internal_modes[2],
        climate.const.HVAC_MODE_FAN_ONLY: internal_modes[3],
        climate.const.HVAC_MODE_HEAT: internal_modes[4],
    }

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        if domain == climate.DOMAIN:
            operation_list = attributes.get(climate.ATTR_HVAC_MODES)
            for operation in operation_list:
                if operation in ThermostatCapability.climate_map:
                    return True
        return False

    def parameters_default(self) -> Dict[str, Any]:
        """Return parameters for a devices request."""
        operation_list = self.state.attributes.get(climate.ATTR_HVAC_MODES)
        modes = []
        for operation in sorted(operation_list):
            if operation in self.climate_map:
                modes.append({'value': self.climate_map[operation]})

        return {
            'instance': self.instance,
            'modes': modes,
        }

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        operation = self.state.attributes.get(climate.ATTR_HVAC_MODE)

        if operation is not None and operation in self.climate_map:
            return self.climate_map[operation]

        # Return first value if current one is not acceptable
        for operation in self.state.attributes.get(climate.ATTR_HVAC_MODES):
            if operation in self.climate_map:
                return self.climate_map[operation]

        return 'auto'

    async def set_state_default(self, data: 'RequestData', state: Dict):
        """Set device state."""
        value = None
        for climate_value, yandex_value in self.climate_map.items():
            if yandex_value == state['value']:
                value = climate_value
                break

        if value is None:
            raise SmartHomeError(ERR_INVALID_VALUE, "Unacceptable value")

        await self.hass.services.async_call(
            climate.DOMAIN,
            climate.SERVICE_SET_HVAC_MODE, {
                ATTR_ENTITY_ID: self.state.entity_id,
                climate.ATTR_HVAC_MODE: value
            }, blocking=True, context=data.context)


@register_capability
class FanSpeedCapability(_ModeCapability):
    """Fan speed functionality."""

    instance = 'fan_speed'
    internal_modes = ("auto", "low", "medium", "high", "turbo")

    values = {
        internal_modes[0]: ['auto'],
        internal_modes[1]: ['low', 'min', 'silent'],
        internal_modes[2]: ['medium', 'middle'],
        internal_modes[3]: ['high', 'max', 'strong', 'favorite'],
    }

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        if domain == climate.DOMAIN:
            return features & climate.SUPPORT_FAN_MODE
        elif domain == fan.DOMAIN:
            return features & fan.SUPPORT_SET_SPEED
        return False

    def parameters_default(self) -> Dict[str, Any]:
        """Return parameters for a devices request."""
        if self.state.domain == climate.DOMAIN:
            speed_list = self.state.attributes.get(climate.ATTR_FAN_MODES)
        elif self.state.domain == fan.DOMAIN:
            speed_list = self.state.attributes.get(fan.ATTR_SPEED_LIST)
        else:
            speed_list = []

        speeds = []
        added = []
        for ha_value in speed_list:
            value = self.get_yandex_value_by_ha_value(ha_value)
            if value is not None and value not in added:
                speeds.append({'value': value})
                added.append(value)

        return {
            'instance': self.instance,
            'modes': speeds,
            'ordered': True
        }

    def get_yandex_value_by_ha_value(self, ha_value):
        for yandex_value, names in self.values.items():
            for name in names:
                if ha_value.lower().find(name) != -1:
                    return yandex_value
        return None

    def get_ha_by_yandex_value(self, yandex_value):
        if self.state.domain == climate.DOMAIN:
            speed_list = self.state.attributes.get(climate.ATTR_FAN_MODES)

        elif self.state.domain == fan.DOMAIN:
            speed_list = self.state.attributes.get(fan.ATTR_SPEED_LIST)

        else:
            speed_list = []

        for ha_value in speed_list:
            if yandex_value in self.values:
                for name in self.values[yandex_value]:
                    if ha_value.lower().find(name) != -1:
                        return ha_value
        return None

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        if self.state.domain == climate.DOMAIN:
            ha_value = self.state.attributes.get(climate.ATTR_FAN_MODE)
        elif self.state.domain == fan.DOMAIN:
            ha_value = self.state.attributes.get(fan.ATTR_SPEED)
        else:
            ha_value = None

        if ha_value is not None:
            yandex_value = self.get_yandex_value_by_ha_value(ha_value)
            if yandex_value is not None:
                return yandex_value

        return 'auto'

    async def set_state_default(self, data: 'RequestData', state: Dict):
        """Set device state."""
        value = self.get_ha_by_yandex_value(state['value'])

        if value is None:
            raise SmartHomeError(ERR_INVALID_VALUE, "Unsupported value")

        if self.state.domain == climate.DOMAIN:
            service = climate.SERVICE_SET_FAN_MODE
            attr = climate.ATTR_FAN_MODE

        elif self.state.domain == fan.DOMAIN:
            service = fan.SERVICE_SET_SPEED
            attr = fan.ATTR_SPEED

        else:
            raise SmartHomeError(ERR_INVALID_VALUE, "Unsupported domain")

        await self.hass.services.async_call(
            self.state.domain,
            service, {
                ATTR_ENTITY_ID: self.state.entity_id,
                attr: value
            }, blocking=True, context=data.context)


@register_capability
class CleanupModeCapability(_ModeCapability):
    """Cleanup mode functionality."""

    instance = "cleanup_mode"
    internal_modes = (
        "auto",
        "eco",
        "express",
        "normal",
        "quiet"
    )

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return False


@register_capability
class SwingCapability(_ModeCapability):
    """Swing capability"""

    instance = "swing"

    modes_swing = {
        climate.const.SWING_BOTH: "auto",
        climate.const.SWING_HORIZONTAL: "horizontal",
        climate.const.SWING_OFF: "stationary",
        climate.const.SWING_VERTICAL: "vertical",
    }

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return domain == climate.DOMAIN and \
            features & climate.SUPPORT_SWING_MODE

    def parameters_default(self) -> Dict[str, Any]:
        """Return parameters for a devices request."""
        swing_modes = self.state.attributes.get(climate.const.ATTR_SWING_MODES)
        modes = []
        for mode in sorted(swing_modes):
            if mode in self.modes_swing:
                modes.append({'value': self.modes_swing.get(mode)})

        return {
            'instance': self.instance,
            'modes': modes,
        }

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        return self.modes_swing.get(
            self.state.attributes(climate.const.ATTR_SWING_MODE),
            climate.const.SWING_OFF
        )

    async def set_state_default(self, data: 'RequestData', state: dict):
        for hass_mode, yandex_mode in self.modes_swing.items():
            if yandex_mode == state['value'] and hass_mode in self.state.attributes.get(climate.const.ATTR_SWING_MODES):
                await self.hass.services.async_call(
                    climate.DOMAIN,
                    climate.SERVICE_SET_SWING_MODE, {
                        ATTR_ENTITY_ID: self.state.entity_id,
                        climate.const.ATTR_SWING_MODE: hass_mode
                    }, blocking=True, context=data.context)
                return

        raise SmartHomeError(ERR_INVALID_VALUE, "Unsupported swing mode")


class _RangeCapability(_Capability):
    """Base class of capabilities with range functionality like volume or
    brightness.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-docpage/
    """

    type = CAPABILITIES_RANGE
    unit: Optional[str] = NotImplemented
    retrievable = True

    @property
    def min_max_precision(self) -> Optional[Tuple[Union[int, float], Union[int, float], Union[int, float]]]:
        return None

    @property
    def random_access(self) -> bool:
        return True

    @classmethod
    def has_override(cls, domain: str, entity_config: Dict, attributes: Dict) -> bool:
        """Determine whether mode capability has an override."""
        return bool(cls.get_override_config(entity_config))

    @classmethod
    def get_override_config(cls, entity_config: Dict) -> Optional[Dict[str, Any]]:
        """Return override entity ID for modes."""
        modes_config = entity_config.get(CONF_ENTITY_RANGES)
        if modes_config:
            return modes_config.get(cls.instance)

    def parameters_default(self) -> Dict[str, Any]:
        """Return parameters for a devices request."""
        parameters = {
            "instance": self.instance,
            "random_access": self.random_access,
        }

        min_max_precision = self.min_max_precision
        if min_max_precision is not None:
            parameters['range'] = dict(zip(['min', 'max', 'precision'], min_max_precision))

        if self.unit is not None:
            parameters['unit'] = self.unit

        return parameters

    def parameters_override(self) -> Dict[str, Any]:
        override_config = self.get_override_config(self.entity_config)

        parameters = {
            "instance": self.instance,
            "random_access": True,
            "range": {
                "max": override_config[CONF_MAXIMUM],
                "min": override_config[CONF_MINIMUM],
                "precision": override_config[CONF_PRECISION],
            }
        }

        if self.unit:
            parameters['unit'] = self.unit

        return parameters

    def get_value_override(self) -> Optional[Union[str, float, int]]:
        override_config = self.get_override_config(self.entity_config)

        override_entity_state = self.hass.states.get(override_config[CONF_ENTITY_ID])
        if override_entity_state:
            try:
                source_state = float(override_entity_state)

            except ValueError:
                source_state = 0

            value = source_state / override_config[CONF_MULTIPLIER]

            return min(override_config[CONF_MAXIMUM], max(override_config[CONF_MINIMUM], value))

        return override_config[CONF_MINIMUM]

    async def set_state_override(self, data: 'RequestData', state: Dict):
        override_config = self.get_override_config(self.entity_config)
        value = float(state['value']) * override_config[CONF_MULTIPLIER]
        script_object = Script(self.hass, override_config[CONF_SET_SCRIPT])

        await script_object.async_run({
            'value': value,
            'entity_id': override_config[CONF_ENTITY_ID]
        }, context=data.context)


@register_capability
class HumidityCapability(_RangeCapability):
    """Set humidity functionality."""

    instance = 'humidity'
    unit = "unit.percent"

    ATTR_TARGET_HUMIDITY = "target_humidity"
    ATTR_CURRENT_HUMIDITY = "current_humidity"
    ATTR_HUMIDITY_STEP = "humidity_step"
    ATTR_SERVICE_SET_HUMIDITY = "set_humidity"
    ATTR_MIN_HUMIDITY = "min_humidity"
    ATTR_MAX_HUMIDITY = "max_humidity"
    SERVICE_PARAMS = "service_config"

    supported_humidifiers = {
        climate.DOMAIN: [
            {  # Default entity support
                ATTR_TARGET_HUMIDITY: climate.ATTR_HUMIDITY,
                ATTR_CURRENT_HUMIDITY: climate.ATTR_CURRENT_HUMIDITY,
                ATTR_SERVICE_SET_HUMIDITY: (climate.DOMAIN, climate.SERVICE_SET_HUMIDITY),
                ATTR_MIN_HUMIDITY: climate.ATTR_MIN_HUMIDITY,
                ATTR_MAX_HUMIDITY: climate.ATTR_MAX_HUMIDITY,
                ATTR_HUMIDITY_STEP: 1,
                SERVICE_PARAMS: lambda humidity: {climate.ATTR_HUMIDITY: humidity}
            }
        ],
    }

    def __init__(self, hass: HomeAssistantType, state: State, entity_config):
        super().__init__(hass, state, entity_config)

        parameters = self._get_access_parameters(state.domain, state.attributes)
        if parameters is None:
            raise ValueError('Unsupported entity state')

        domain, attributes = parameters
        self._service_domain = domain
        self._attrs = attributes

    @classmethod
    def _get_access_parameters(cls, domain: str, attributes: Dict[str, Any]) -> Optional[dict]:
        access_parameters = cls.supported_humidifiers.get(domain)
        if access_parameters:
            for attr_config in access_parameters:
                if all([attr_config[a] in attributes for a in [cls.ATTR_CURRENT_HUMIDITY, cls.ATTR_TARGET_HUMIDITY]]):
                    return attr_config

    def _get_entity_attribute(self, attribute_type: str):
        """
        Get attribute from skimmed entity attributes.
        :param attribute_type: Attribute from supported attributes
        :return:
        """
        return self.state.attributes.get(self._attrs[attribute_type])

    @property
    def min_max_precision(self) -> Tuple[Union[int, float], Union[int, float], Union[int, float]]:
        """Return min / max / precision values."""
        return (
            self._get_entity_attribute(self.ATTR_MIN_HUMIDITY),
            self._get_entity_attribute(self.ATTR_MAX_HUMIDITY),
            self._get_entity_attribute(self.ATTR_HUMIDITY_STEP)
        )

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        return bool(cls._get_access_parameters(domain, attributes))

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        return self._get_entity_attribute(self.ATTR_CURRENT_HUMIDITY)

    async def set_state_default(self, data: 'RequestData', state: Dict) -> None:
        """
        Set target humidity (default variant).
        :param data: Request data
        :param state: Requested state
        """
        domain, service = self._attrs[climate.SERVICE_SET_HUMIDITY]

        service_params = {ATTR_ENTITY_ID: self.state.entity_id}
        service_params.update(self._attrs[self.SERVICE_PARAMS](state['value']))

        self.hass.services.async_call(domain, service, service_params, blocking=True, context=data.context)


@register_capability
class TemperatureCapability(_RangeCapability):
    """Set temperature functionality."""

    instance = 'temperature'
    unit = "unit.temperature.celsius"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        if domain == water_heater.DOMAIN:
            return features & water_heater.SUPPORT_TARGET_TEMPERATURE

        elif domain == climate.DOMAIN:
            return features & climate.const.SUPPORT_TARGET_TEMPERATURE

        return False

    @property
    def min_max_precision(self):
        if self.state.domain == water_heater.DOMAIN:
            min_temp = self.state.attributes.get(water_heater.ATTR_MIN_TEMP)
            max_temp = self.state.attributes.get(water_heater.ATTR_MAX_TEMP)
        elif self.state.domain == climate.DOMAIN:
            min_temp = self.state.attributes.get(climate.ATTR_MIN_TEMP)
            max_temp = self.state.attributes.get(climate.ATTR_MAX_TEMP)
        else:
            min_temp = 0
            max_temp = 100

        return min_temp, max_temp, 0.5

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        temperature = None
        if self.state.domain == water_heater.DOMAIN:
            temperature = self.state.attributes.get(water_heater.ATTR_TEMPERATURE)

        elif self.state.domain == climate.DOMAIN:
            temperature = self.state.attributes.get(climate.ATTR_TEMPERATURE)

        if temperature is None:
            return 0

        return float(temperature)

    async def set_state_default(self, data: 'RequestData', state: Dict) -> None:
        """Set device state."""

        if self.state.domain == water_heater.DOMAIN:
            service = water_heater.SERVICE_SET_TEMPERATURE
            attr = water_heater.ATTR_TEMPERATURE

        elif self.state.domain == climate.DOMAIN:
            service = climate.SERVICE_SET_TEMPERATURE
            attr = climate.ATTR_TEMPERATURE

        else:
            raise SmartHomeError(ERR_INVALID_VALUE, "Unsupported domain")

        await self.hass.services.async_call(
            self.state.domain,
            service, {
                ATTR_ENTITY_ID: self.state.entity_id,
                attr: state['value']
            }, blocking=True, context=data.context)


@register_capability
class BrightnessCapability(_RangeCapability):
    """Set brightness functionality."""

    instance = 'brightness'
    unit = "unit.percent"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        return domain == light.DOMAIN and features & light.SUPPORT_BRIGHTNESS

    @property
    def min_max_precision(self) -> Tuple[Union[int, float], Union[int, float], Union[int, float]]:
        return 0, 100, 1

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        brightness = self.state.attributes.get(light.ATTR_BRIGHTNESS)
        if brightness is None:
            return 0

        return int(100 * (brightness / 255))

    async def set_state_default(self, data: 'RequestData', state: Dict):
        """Set device state."""
        await self.hass.services.async_call(
            light.DOMAIN,
            light.SERVICE_TURN_ON, {
                ATTR_ENTITY_ID: self.state.entity_id,
                light.ATTR_BRIGHTNESS_PCT: state['value']
            }, blocking=True, context=data.context)


@register_capability
class VolumeCapability(_RangeCapability):
    """Set volume functionality."""

    instance = 'volume'
    unit = None

    def __init__(self, hass: HomeAssistantType, state: State, entity_config: Dict[str, Any]):
        super().__init__(hass, state, entity_config)
        features = self.state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        self.retrievable = (
                self.has_override(state.domain, entity_config, state.attributes)
                or features & media_player.SUPPORT_VOLUME_SET != 0
        )

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        return domain == media_player.DOMAIN and features & media_player.SUPPORT_VOLUME_STEP

    @property
    def random_access(self) -> bool:
        return not self.is_relative_volume_only()

    @property
    def min_max_precision(self) -> Tuple[Union[int, float], Union[int, float], Union[int, float]]:
        return None if self.is_relative_volume_only() else (0, 100, 1)

    def is_relative_volume_only(self):
        return not self.retrievable or self.entity_config.get(
            CONF_RELATIVE_VOLUME_ONLY)

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        level = self.state.attributes.get(
            media_player.ATTR_MEDIA_VOLUME_LEVEL)
        if level is None:
            return 0
        else:
            return int(level * 100)

    async def set_state_default(self, data: 'RequestData', state: Dict):
        """Set device state."""
        if self.is_relative_volume_only():
            if state['value'] > 0:
                service = media_player.SERVICE_VOLUME_UP
            else:
                service = media_player.SERVICE_VOLUME_DOWN
            await self.hass.services.async_call(
                media_player.DOMAIN,
                service, {
                    ATTR_ENTITY_ID: self.state.entity_id
                }, blocking=True, context=data.context)
        else:
            await self.hass.services.async_call(
                media_player.DOMAIN,
                media_player.SERVICE_VOLUME_SET, {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    media_player.const.ATTR_MEDIA_VOLUME_LEVEL:
                        state['value'] / 100,
                }, blocking=True, context=data.context)


@register_capability
class ChannelCapability(_RangeCapability):
    """Set channel functionality."""

    instance = 'channel'
    unit = None

    script_channel_up = None
    script_channel_down = None

    def __init__(self, hass, state, config):
        super().__init__(hass, state, config)
        features = self.state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        self.retrievable = features & media_player.SUPPORT_PLAY_MEDIA != 0 and \
            self.entity_config.get(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID)

        channel_up = config.get(CONF_SCRIPT_CHANNEL_UP)
        if channel_up:
            self.script_channel_up = Script(hass, channel_up)

        channel_down = config.get(CONF_SCRIPT_CHANNEL_DOWN)
        if channel_down:
            self.script_channel_down = Script(hass, channel_down)

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        if domain == media_player.DOMAIN:
            return (features & media_player.SUPPORT_PLAY_MEDIA and
                    entity_config.get(CONF_CHANNEL_SET_VIA_MEDIA_CONTENT_ID) and
                    (features & media_player.SUPPORT_PREVIOUS_TRACK or
                     entity_config.get(CONF_SCRIPT_CHANNEL_DOWN)) and
                    (features & media_player.SUPPORT_NEXT_TRACK) or
                    entity_config.get(CONF_SCRIPT_CHANNEL_UP))

        return False

    @property
    def min_max_precision(self) -> Optional[Tuple[Union[int, float], Union[int, float], Union[int, float]]]:
        return (0, 999, 1) if self.retrievable else None

    @property
    def random_access(self) -> bool:
        return self.retrievable

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        if not self.retrievable or self.state.attributes.get(
                media_player.ATTR_MEDIA_CONTENT_TYPE) \
                != media_player.const.MEDIA_TYPE_CHANNEL:
            return 0

        try:
            return int(self.state.attributes.get(
                media_player.ATTR_MEDIA_CONTENT_ID))

        except ValueError:
            return 0

        except TypeError:
            return 0

    async def set_state_default(self, data: 'RequestData', state: Dict):
        """Set device state."""
        if 'relative' in state and state['relative']:
            if state['value'] > 0:
                if self.script_channel_up:
                    await self.script_channel_up.async_run({
                        ATTR_ENTITY_ID: self.state.entity_id,
                    }, context=data.context)
                    return
                else:
                    service = media_player.SERVICE_MEDIA_NEXT_TRACK
            else:
                if self.script_channel_down:
                    await self.script_channel_down.async_run({
                        ATTR_ENTITY_ID: self.state.entity_id,
                    }, context=data.context)
                    return
                else:
                    service = media_player.SERVICE_MEDIA_PREVIOUS_TRACK

            await self.hass.services.async_call(
                media_player.DOMAIN,
                service, {
                    ATTR_ENTITY_ID: self.state.entity_id
                }, blocking=True, context=data.context)

        else:
            await self.hass.services.async_call(
                media_player.DOMAIN,
                media_player.SERVICE_PLAY_MEDIA, {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    media_player.const.ATTR_MEDIA_CONTENT_ID: state['value'],
                    media_player.const.ATTR_MEDIA_CONTENT_TYPE:
                        media_player.const.MEDIA_TYPE_CHANNEL,
                }, blocking=True, context=data.context)


@register_capability
class OpenCapability(_RangeCapability):
    instance = "open"
    unit = None

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        if domain == cover.DOMAIN:
            return features & cover.SUPPORT_SET_POSITION

        return False

    @property
    def min_max_precision(self) -> Optional[Tuple[Union[int, float], Union[int, float], Union[int, float]]]:
        return 0, 100, 1

    @property
    def random_access(self) -> bool:
        return True

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        return self.state.attributes.get(cover.ATTR_CURRENT_POSITION)

    async def set_state_default(self, data: 'RequestData', state: Dict):
        await self.hass.services.async_call(
            cover.DOMAIN,
            cover.SERVICE_SET_COVER_POSITION, {
                ATTR_ENTITY_ID: self.state.entity_id,
                cover.ATTR_POSITION: state['value']
            }, blocking=True, context=data.context)


class _ColorSettingCapability(_Capability):
    """Base color setting functionality.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/
    """

    type = CAPABILITIES_COLOR_SETTING

    def parameters_default(self):
        """Return parameters for a devices request."""
        result = {}

        features = self.state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        if features & light.SUPPORT_COLOR:
            result['color_model'] = 'rgb'

        if features & light.SUPPORT_COLOR_TEMP:
            max_temp = self.state.attributes[light.ATTR_MIN_MIREDS]
            min_temp = self.state.attributes[light.ATTR_MAX_MIREDS]
            result['temperature_k'] = {
                'min': color_util.color_temperature_mired_to_kelvin(min_temp),
                'max': color_util.color_temperature_mired_to_kelvin(max_temp)
            }

        return result

    @classmethod
    def has_override(cls, domain: str, entity_config: Dict, attributes: Dict) -> bool:
        return False


@register_capability
class RgbCapability(_ColorSettingCapability):
    """RGB color functionality."""

    instance = 'rgb'

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        return domain == light.DOMAIN and features & light.SUPPORT_COLOR

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        color = self.state.attributes.get(light.ATTR_RGB_COLOR)
        if color is None:
            return 0

        rgb = color[0]
        rgb = (rgb << 8) + color[1]
        rgb = (rgb << 8) + color[2]

        return rgb

    async def set_state_default(self, data: 'RequestData', state: Dict) -> None:
        """Set device state."""
        red = (state['value'] >> 16) & 0xFF
        green = (state['value'] >> 8) & 0xFF
        blue = state['value'] & 0xFF

        await self.hass.services.async_call(
            light.DOMAIN,
            light.SERVICE_TURN_ON, {
                ATTR_ENTITY_ID: self.state.entity_id,
                light.ATTR_RGB_COLOR: (red, green, blue)
            }, blocking=True, context=data.context)


@register_capability
class TemperatureKCapability(_ColorSettingCapability):
    """Color temperature functionality."""

    instance = 'temperature_k'

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        """Test if state is supported."""
        return domain == light.DOMAIN and features & light.SUPPORT_COLOR_TEMP

    def get_value_default(self) -> Optional[Union[str, float, int]]:
        """Return the state value of this capability for this entity."""
        kelvin = self.state.attributes.get(light.ATTR_COLOR_TEMP)
        if kelvin is None:
            return 0

        return color_util.color_temperature_mired_to_kelvin(kelvin)

    async def set_state_default(self, data: 'RequestData', state: Dict) -> None:
        """Set device state."""
        await self.hass.services.async_call(
            light.DOMAIN,
            light.SERVICE_TURN_ON, {
                ATTR_ENTITY_ID: self.state.entity_id,
                light.ATTR_KELVIN: state['value']
            }, blocking=True, context=data.context)
