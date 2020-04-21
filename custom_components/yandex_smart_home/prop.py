"""Implement the Yandex Smart Home properties."""
import logging
from typing import Dict, Any

from custom_components.yandex_smart_home.const import ERR_NOT_SUPPORTED_IN_CURRENT_MODE
from custom_components.yandex_smart_home.error import SmartHomeError
from homeassistant.components import (
    climate,
    sensor,
    switch,
    air_quality,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    POWER_WATT,
)

from .const import (
    CONF_ENTITY_PROPERTIES,
    CONF_ENTITY_PROPERTY_TYPE,
    CONF_ENTITY_PROPERTY_ENTITY,
    CONF_ENTITY_PROPERTY_ATTRIBUTE,
    ATTR_CURRENT_POWER_W,
    ATTR_WATER_LEVEL,
    UNIT_VOLT,
    UNIT_KILOVOLT,
    UNIT_MEGAVOLT,
    UNIT_MILLIVOLT,
    UNIT_AMPERE,
)

_LOGGER = logging.getLogger(__name__)

PREFIX_PROPERTIES = 'devices.properties.'
PROPERTY_FLOAT = PREFIX_PROPERTIES + 'float'

PROPERTIES = []


def register_property(property):
    """Decorate a function to register a property."""
    PROPERTIES.append(property)
    return property


class _Property(object):
    """Represents a Property."""
    unit = ''
    type = ''
    instance = ''
    supported_sensor_units = []
    default_value = None

    def __init__(self, hass, state, entity_config):
        """Initialize a trait for a state."""
        self.hass = hass
        self.state = state
        self.entity_config = entity_config

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        raise NotImplementedError("Properties must implement this!")

    @classmethod
    def has_override(cls, domain: str, entity_config: Dict, attributes: Dict) -> bool:
        entity_properties = entity_config.get(CONF_ENTITY_PROPERTIES)
        return bool(entity_properties) and bool(entity_properties.get(cls.instance))

    def description(self):
        """Return description for a devices request."""
        response = {
            'type': self.type,
            'retrievable': True,
        }
        parameters = self.parameters()
        if parameters is not None:
            response['parameters'] = parameters

        return response

    def get_state(self):
        """Return the state of this property for this entity."""
        return {
            'type': self.type,
            'state': {
                'instance': self.instance,
                'value': self.get_value()
            }
        }

    def parameters(self):
        return {
            'instance': self.instance,
            'unit': self.unit
        }

    def get_value(self):
        """Return the state value of this capability for this entity."""
        state = self.state
        if self.has_override(state.domain, self.entity_config, state.attributes):
            return self.get_value_override()
        if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN) and self.default_value is not None:
            return self.default_value
        return self.get_value_default()
    
    def get_value_default(self) -> Any:
        raise NotImplementedError("Properties must implement this!")

    def get_value_override(self) -> Any:
        raise NotImplementedError("Properties must implement this!")


class _FloatProperty(_Property):
    """Represents base class for float properties."""
    type = PROPERTY_FLOAT
    default_value = 0.0

    def get_value_default(self) -> float:
        return float(self.state.state)

    def get_value_override(self) -> float:
        attribute = None
        property_config = self.entity_config[CONF_ENTITY_PROPERTIES][self.instance]

        if CONF_ENTITY_PROPERTY_ENTITY in property_config:
            property_entity_id = property_config.get(CONF_ENTITY_PROPERTY_ENTITY)
            state = self.hass.states.get(property_entity_id)
        else:
            state = self.state

        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return 0.0
        
        if CONF_ENTITY_PROPERTY_ATTRIBUTE in property_config:
            attribute = property_config.get(CONF_ENTITY_PROPERTY_ATTRIBUTE)
            return float(state.get(attribute, 0.0))

        return float(state.state)

@register_property
class TemperatureProperty(_FloatProperty):
    """Temperature property"""
    instance = 'temperature'
    unit = 'unit.temperature.celsius'

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        if domain == sensor.DOMAIN:
            return attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_TEMPERATURE
        elif domain == climate.DOMAIN:
            return attributes.get(climate.ATTR_CURRENT_TEMPERATURE) is not None

        return False

    def get_value_default(self) -> float:
        value = 0.0
        if self.state.domain == sensor.DOMAIN:
            value = self.state.state
        elif self.state.domain == climate.DOMAIN:
            value = self.state.attributes.get(climate.ATTR_CURRENT_TEMPERATURE)
        return float(value)


@register_property
class HumidityProperty(_FloatProperty):
    """Humidity property."""
    instance = "humidity"
    unit = "unit.percent"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        if domain == sensor.DOMAIN:
            return attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_HUMIDITY
        elif domain == climate.DOMAIN:
            return attributes.get(climate.ATTR_CURRENT_HUMIDITY) is not None

        return False

    def get_value_default(self):
        value = 0
        if self.state.domain == sensor.DOMAIN:
            value = self.state.state
        elif self.state.domain == climate.DOMAIN:
            value = self.state.attributes.get(climate.ATTR_CURRENT_HUMIDITY)
        return float(value)


@register_property
class WaterLevelProperty(_FloatProperty):
    """Water level property."""
    instance = "water_level"
    unit = "unit.percent"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return attributes.get(ATTR_WATER_LEVEL) is not None
    
    def get_value_default(self):
        return float(self.state.attributes.get(ATTR_WATER_LEVEL, 0.0))


@register_property
class CO2LevelProperty(_FloatProperty):
    """Water level property."""
    instance = "co2_level"
    unit = "unit.ppm"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return domain == air_quality.DOMAIN and \
            attributes.get(air_quality.ATTR_CO2) is not None
    
    def get_value_default(self):
        return float(self.state.attributes.get(air_quality.ATTR_CO2, 0.0))


@register_property
class PowerProperty(_FloatProperty):
    """Current power property."""
    instance = "power"
    unit = "unit.watt"

    supported_sensor_units = [
        POWER_WATT,
        f'k{POWER_WATT}',
    ]

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        if domain == sensor.DOMAIN:
            return attributes.get(ATTR_UNIT_OF_MEASUREMENT) in cls.supported_sensor_units

        return attributes.get(ATTR_CURRENT_POWER_W) is not None

    def get_value_default(self):
        if self.state.domain == sensor.DOMAIN:
            unit_of_measurement = self.state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

            if unit_of_measurement is None or unit_of_measurement == POWER_WATT:
                return float(self.state.state)
            elif unit_of_measurement == 'k' + POWER_WATT:
                return float(self.state.state) / 1000.0

        return float(self.state.attributes(ATTR_CURRENT_POWER_W, 0.0))


@register_property
class VoltageProperty(_FloatProperty):
    """Voltage property."""
    instance = "voltage"
    unit = "unit.volt"

    supported_sensor_units = [UNIT_VOLT, UNIT_KILOVOLT, UNIT_MEGAVOLT, UNIT_MILLIVOLT]

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return domain == sensor.DOMAIN and \
            attributes.get(ATTR_UNIT_OF_MEASUREMENT) in cls.supported_sensor_units

    def get_value_default(self) -> float:
        unit_of_measurement = self.state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit_of_measurement == UNIT_MEGAVOLT:
            return float(self.state.state) / 1000000.0
        elif unit_of_measurement == UNIT_KILOVOLT:
            return float(self.state.state) / 1000.0
        elif unit_of_measurement == UNIT_MILLIVOLT:
            return float(self.state.state) * 1000.0
        return float(self.state.state)


@register_property
class AmperageProperty(_FloatProperty):
    """Voltage property."""
    instance = "amperage"
    unit = "unit.ampere"

    @classmethod
    def supported(cls, domain: str, features: int, entity_config: Dict, attributes: Dict) -> bool:
        return domain == sensor.DOMAIN and \
            attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UNIT_AMPERE

    def get_value_default(self) -> float:
        return float(self.state.state)