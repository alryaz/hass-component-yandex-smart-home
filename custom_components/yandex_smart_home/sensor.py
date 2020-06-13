from typing import Optional, Dict, Any, Union, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OK
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    DOMAIN,
    ATTR_LAST_SYNC_TIME,
    ATTR_LAST_ACTION_TIME,
    ATTR_LAST_ACTION_TARGETS,
    ATTR_SYNCED_DEVICES_COUNT, ATTR_YANDEX_TYPE
)

if TYPE_CHECKING:
    from datetime import datetime


# noinspection PyUnusedLocal
async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry, async_add_entities):
    """Add Yandex statistics sensor."""
    async_add_entities(
        [YandexStatisticsSensor()],
        False
    )

    return True


class YandexStatisticsSensor(Entity):
    def __init__(self) -> None:
        """Initialize the device mixin."""
        self._last_action_targets = None
        self._last_action_time = None
        self._last_sync_time = None
        self._synced_devices_count = None

        self._identifier = (DOMAIN, "status")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        if self.hass.data.get(DOMAIN):
            self.hass.data[DOMAIN].sensor_status = self

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self.hass.data.get(DOMAIN):
            self.hass.data[DOMAIN].sensor_status = None

    def record_action(self, datetime_at: 'datetime', targets) -> None:
        """Shorthand method for action recording."""
        self._last_action_time = str(datetime_at)
        self._last_action_targets = list(targets.keys())
        self.schedule_update_ha_state()

    def record_sync(self, datetime_at: 'datetime', devices) -> None:
        self._last_sync_time = str(datetime_at)
        self._synced_devices_count = len(devices)
        self.schedule_update_ha_state()

    @property
    def name(self) -> Optional[str]:
        return "Yandex Smart Home Status"

    @property
    def icon(self) -> Optional[str]:
        return 'mdi:cloud'

    @property
    def state(self) -> Union[None, str, int, float]:
        return STATE_OK

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        return {
            ATTR_LAST_SYNC_TIME: self._last_sync_time,
            ATTR_LAST_ACTION_TIME: self._last_action_time,
            ATTR_LAST_ACTION_TARGETS: self._last_action_targets,
            ATTR_SYNCED_DEVICES_COUNT: self._synced_devices_count,
            ATTR_YANDEX_TYPE: False,
        }

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self) -> Optional[str]:
        return "%s_%s" % self._identifier
