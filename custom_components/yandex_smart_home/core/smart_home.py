"""Support for Yandex Smart Home API."""
import logging
from datetime import datetime

from homeassistant.const import CLOUD_NEVER_EXPOSED_ENTITIES
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util.decorator import Registry

from ..const import (
    ERR_INTERNAL_ERROR, ERR_DEVICE_UNREACHABLE,
    ERR_DEVICE_NOT_FOUND, ATTR_YANDEX_TYPE
)
from ..core.error import SmartHomeError
from ..core.helpers import RequestData, YandexEntity

HANDLERS = Registry()
_LOGGER = logging.getLogger(__name__)


async def async_handle_message(hass: HomeAssistantType, config, user_id, request_id, action,
                               message):
    """Handle incoming API messages."""
    data = RequestData(config, user_id, request_id)

    response = await _process(hass, data, action, message)

    if response and 'payload' in response and 'error_code' in response['payload']:
        _LOGGER.error('Error handling message %s: %s',
                      message, response['payload'])

    return response


async def _process(hass: HomeAssistantType, data: RequestData, action, message):
    """Process a message."""
    handler = HANDLERS.get(action)

    if handler is None:
        return {
            'request_id': data.request_id,
            'payload': {'error_code': ERR_INTERNAL_ERROR}
        }

    # noinspection PyBroadException
    try:
        result = await handler(hass, data, message)

    except SmartHomeError as err:
        return {
            'request_id': data.request_id,
            'payload': {'error_code': err.code}
        }

    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception('Unexpected error')
        return {
            'request_id': data.request_id,
            'payload': {'error_code': ERR_INTERNAL_ERROR}
        }

    if result is None:
        if data.request_id is None:
            return None

        return {'request_id': data.request_id}

    return {'request_id': data.request_id, 'payload': result}


# noinspection PyUnusedLocal
@HANDLERS.register('/user/devices')
async def async_devices_sync(hass: HomeAssistantType, data: RequestData, message):
    """Handle /user/devices request.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/reference/get-devices-docpage/

    :param hass: HomeAssistant object
    :param data: Request data
    :param message: Message contents
    :return: Optional response
    """
    devices = []
    for state in hass.states.async_all():
        if state.entity_id in CLOUD_NEVER_EXPOSED_ENTITIES:
            continue

        if state.attributes.get(ATTR_YANDEX_TYPE) is False:
            continue

        if not data.config.should_expose(state.entity_id):
            continue

        entity = YandexEntity(hass, data.config, state)
        serialized = await entity.devices_serialize()

        if serialized is None:
            _LOGGER.debug("No mapping for %s domain", entity.state)
            continue

        devices.append(serialized)

    response = {
        'user_id': data.context.user_id,
        'devices': devices,
    }

    return response


# noinspection PyUnusedLocal
@HANDLERS.register('/user/devices/query')
async def async_devices_query(hass: HomeAssistantType, data: RequestData, message):
    """Handle /user/devices/query request.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/reference/post-devices-query-docpage/

    :param hass: HomeAssistant object
    :param data: Request data
    :param message: Message contents
    :return: Optional response
    """
    devices = []
    for device in message.get('devices', []):
        entity_id = device['id']

        if not data.config.should_expose(entity_id):
            devices.append({
                'id': entity_id,
                'error_code': ERR_DEVICE_NOT_FOUND,
            })
            continue

        state = hass.states.get(entity_id)

        if not state or state.attributes.get(ATTR_YANDEX_TYPE) is False:
            # If we can't find a state, the device is unreachable
            devices.append({
                'id': entity_id,
                'error_code': ERR_DEVICE_UNREACHABLE
            })
            continue

        entity = YandexEntity(hass, data.config, state)
        devices.append(entity.query_serialize())

    yandex_sensor = data.config.sensor_status
    if yandex_sensor:
        yandex_sensor.record_sync(datetime.now(), devices)

    return {'devices': devices}


# noinspection PyUnusedLocal
@HANDLERS.register('/user/devices/action')
async def handle_devices_execute(hass: HomeAssistantType, data: RequestData, message):
    """Handle /user/devices/action request.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/reference/post-action-docpage/

    :param hass: HomeAssistant object
    :param data: Request data
    :param message: Message contents
    :return: Optional response
    """
    entities = {}
    devices = {}
    results = {}
    action_errors = {}

    for device in message['payload']['devices']:
        entity_id = device['id']
        devices[entity_id] = device

        if entity_id not in entities:
            if not data.config.should_expose(entity_id):
                results[entity_id] = {
                    'id': entity_id,
                    'error_code': ERR_DEVICE_NOT_FOUND,
                }
                continue

            state = hass.states.get(entity_id)

            if not state:
                results[entity_id] = {
                    'id': entity_id,
                    'error_code': ERR_DEVICE_UNREACHABLE,
                }
                continue

            entities[entity_id] = YandexEntity(hass, data.config, state)

        for capability in device['capabilities']:
            try:
                await entities[entity_id].execute(data,
                                                  capability.get('type', ''),
                                                  capability.get('state', {}))
            except SmartHomeError as err:
                _LOGGER.error("%s: %s" % (err.code, err.message))
                if entity_id not in action_errors:
                    action_errors[entity_id] = {}
                action_errors[entity_id][capability['type']] = err.code

    final_results = list(results.values())

    for entity in entities.values():
        if entity.entity_id in results:
            continue

        entity.async_update()

        capabilities = []
        for capability in devices[entity.entity_id]['capabilities']:
            if capability['state'] is None or 'instance' not in capability[
                    'state']:
                continue
            if entity.entity_id in action_errors and capability['type'] in \
                    action_errors[entity.entity_id]:
                capabilities.append({
                    'type': capability['type'],
                    'state': {
                        'instance': capability['state']['instance'],
                        'action_result': {
                            'status': 'ERROR',
                            'error_code': action_errors[entity.entity_id][
                                capability['type']],
                        }
                    }
                })
            else:
                capabilities.append({
                    'type': capability['type'],
                    'state': {
                        'instance': capability['state']['instance'],
                        'action_result': {
                            'status': 'DONE',
                        }
                    }
                })

        final_results.append({
            'id': entity.entity_id,
            'capabilities': capabilities,
        })

    yandex_sensor = data.config.sensor_status
    if yandex_sensor:
        yandex_sensor.record_action(datetime.now(), entities)

    return {'devices': final_results}


# noinspection PyUnusedLocal
@HANDLERS.register('/user/unlink')
async def async_devices_disconnect(hass: HomeAssistantType, data: 'RequestData', message):
    """Handle /user/unlink request.

    https://yandex.ru/dev/dialogs/alice/doc/smart-home/reference/unlink-docpage/

    :param hass: HomeAssistant object
    :param data: Request data
    :param message: Message contents
    :return: Optional response
    """
    return None
