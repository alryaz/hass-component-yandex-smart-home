[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

[![Donate](https://img.shields.io/badge/-Donate-purple.svg)](https://money.yandex.ru/to/41001142896898)

## Yandex Smart Home custom component for Home Assistant


### Installation
1. Update home assistant to 0.96.0 at least
1. Configure SSL certificate if it was not done already (***do not*** use self-signed certificate)
1. Create dialog via https://dialogs.yandex.ru/developer/ (see [this section](#create-dialog))
1. Install this component from HACS. That way you get updates automatically. But you also can just copy and add files into custom_components directory manually instead.
1. Restart Home Assistant
1. Follow the example `configuration.yaml` entry below to add integration.
   1. It is also possible to enable this integration via `Settings` => `Integrations` menu within _HomeAssistant_. Search for _Yandex Smart Home_ and follow the activation wizard. Be aware that there are limitations to this method (such as current lack of per-entity configuration).
1. Add devices via your Yandex app on Android/iOS (or in _Testing_ mode).


### Example configuration
```yaml
# Example configuration.yaml entry
yandex_smart_home:
  filter:
    include_domains:
      - switch
      - light
    include_entities:
      - media_player.tv
      - media_player.tv_lg
    exclude_entities:
      - light.highlight
  entity_config:
    switch.kitchen:
      name: CUSTOM_NAME_FOR_YANDEX_SMART_HOME
    light.living_room:
      room: LIVING_ROOM
      toggles:
        backlight: light.wall_ornament
    media_player.tv_lg:
      channel_set_via_media_content_id: true
      sources:
        one: "HDMI 1"
        two: "HDMI 2"
        three: "Composite"
        four: "Netflix App"
      toggles:
        controls_locked: switch.custom_webostv_controls_lock
        backlight: switch.raspberry_pi_ambilight
      properties:
        power:
          entity: sensor.global_power_monitor
          attribute: television_socket
    fan.xiaomi_miio_device:
      name: "Xiaomi Humidifier"
      room: LIVING_ROOM
      type: devices.types.humidifier
      properties:
        temperature: sensor.temperature_123d45678910
        humidity:
          attribute: humidity
        water_level:
          attribute: depth
```


### Variable description
```
yandex_smart_home:
  (map) (Optional) Configuration options for the Yandex Smart Home integration.

  filter:
    (map) (Optional) description: Filters for entities to include/exclude from Yandex Smart Home.
    include_entities:
      (list) (Optional) description: Entity IDs to include.
    include_domains:
      (list) (Optional) Domains to include.
    exclude_entities:
      (list) (Optional) Entity IDs to exclude.
    exclude_domains:
      (list) (Optional) Domains to exclude.

  entity_config:
    (map) (Optional) Entity specific configuration for Yandex Smart Home.
    ENTITY_ID:
      (map) (Optional) Entity to configure.
      name:
        (string) (Optional) Name of entity to show in Yandex Smart Home.
      room:
        (string) (Optional) Associating this device to a room in Yandex Smart Home
      type:
        (string) (Optional) Allows to force set device type. For exmaple set devices.types.purifier to display device as purifier (instead default devices.types.humidifier for such devices) 
      channel_set_via_media_content_id:
        (boolean) (Optional) (media_player only) Enables ability to set channel by number for some TVs
        (TVs that support channel change via passing number as media_content_id)
      relative_volume_only:
        (boolean) (Optional) (media_player only) Force disable ability to get/set volume by number
      sources:
        (dict, boolean) (Optional) (media_player only) Define selectable inputs (or map one-to-one in case of 'true').
        one / two / three / ... / ten:
          (string) (Optional) Source name <=> Input source mapping.
      backlight:
        (string) (Optional) Entity ID to use as backlight control (must be toggleable).
      channel_up:
        (map) (Optional) Script to switch to next channel (avoids using next track).
      channel_down:
        (map) (Optional) Script to switch to previous channel (avoids using previous track).
      toggles:
        (dict) (Optional) Assign togglable entities for certain features or override auto-detected ones.
        backlight / controls_locked ...:
          (entity ID) Entity ID to be used with the toggle
      properties:
        (dict) (Optional) Assign entities or attributes for certain properties or override auto-detected ones.
        humidity / temperature / water_level / co2_level / power / voltage:
          (dict / entity ID) Configuration data for property (only entity ID can be specified instead of dictionary, if using other entities).
          entity:
            (string) (Optional) Custom entity, any sensor can be added 
          attribute:
            (string) (Optional) Attribute of an object to receive data
```


### Overriding exposed entity domain &mdash; `type` option
When exposing device under a domain different from default confirm compatibility by consulting the
[Yandex API documentation](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-types-docpage/) by
comparing sets of capabilities expected from default and target domains. Very common custom exposure would
be rendering a `switch` entity (example above) as a `socket`.

### Room/Area support &mdash; `room` option
Entities that have not got rooms explicitly set and that have been placed in Home Assistant areas will return
room hints to Yandex Smart Home with the devices in those areas. You can always override these manually
by specified a `room` option in corresponding `entity_config` entries.

### Create dialog
Go to https://dialogs.yandex.ru/developer/ and create smart home skill.

Field | Value
------------ | -------------
Endpoint URL | https://[YOUR HOME ASSISTANT URL:PORT]/api/yandex_smart_home

For account linking use button at the bottom of skill settings page, fill it
 using values like below:

Field | Value
------------ | -------------
Client identifier | https://social.yandex.net/
API authorization endpoint | https://[YOUR HOME ASSISTANT URL:PORT]/auth/authorize
Token Endpoint | https://[YOUR HOME ASSISTANT URL:PORT]/auth/token
Refreshing an Access Token | https://[YOUR HOME ASSISTANT URL:PORT]/auth/token

### Supported HomeAssistant domains
_This is a work-in-progress summary, there are more features to mention_
- [x] Automations: `automation`
  - [ ] Matching domain exposure
  - [x] Capabilities:
    - [x] Turn on/off: `on_off`

- [ ] Binary sensors: `binary_sensor`
  - [ ] Matching domain exposure _(no suitable mapping exists yet)_

- [x] Cameras: `camera`
  - [ ] Matching domain exposure
  - [x] Capabilities:
    - [x] Turn on/off: `on_off`

- [x] Climate management: `climate`
  - [x] Matching domain exposure:
    - [x] Default exposure: `thermostat` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-thermostat-docpage/))
    - [x] AC with support for swing: `thermostat.ac` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-thermostat-ac-docpage/))
  - [x] Capabilities:
    - [x] Turn on/off: `on_off`
    - [x] Fan speed setting: `mode.fan_speed`
    - [x] Swing mode setting: `mode.swing`
    - [x] Preset modes: `mode.program`
    - [x] Temperature: `range.temperature`
    - [x] Humidity: `range.humidity`
  - [x] Properties:
    - [x] Current temperature: `float.temperature`
    - [x] Current humidity: `float.humidity`

- [x] Covers: `cover`
  - [x] Matching domain exposure:
    - [x] Default exposure: `openable` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-openable-docpage/))
    - [x] Curtains, blinds, windows, awnings: `openable.curtain` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-openable-docpage/))
  - [x] Capabilities:
    - [x] Toggle open/close: `on_off`
    - [x] Set semi-open state: `range.open`
    - [ ] Set tilt position: _(no suitable mapping exists yet)_

- [x] Fans: `fan`
  - [x] Matching domain exposure:
    - [x] Default exposure: `devices.types.thermostat.ac` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-thermostat-ac-docpage/))
  - [x] Capabilities
    - [x] Turn on/off: `on_off`
    - [x] Fan speed setting: `mode.fan_speed`
    - [ ] Direction setting: _(no suitable mapping exists yet)_

- [x] Lights: `light`
  - [x] Matching domain exposure:
    - [x] Default exposure: `devices.types.light` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-light-docpage/))
  - [x] Capabilities
    - [x] Turn on/off: `on_off`
    - [x] Color setting via RGB: `color_setting.rgb`
    - [ ] Color setting via HSV: `color_setting.hsv` _(unknown whether support is required)_
    - [x] Brightness capability: `range.brightness`
    - [x] Backlight toggle: `toggle.backlight`
    - [x] Effect switching: `mode.program`

- [x] Switches: `switch`
  - [x] Matching domain exposure:
    - [x] Default exposure: `devices.types.switch`
    - [x] Switches with sockets as class: `devices.types.socket`
  - [x] Capabilities:
    - [x] Turn on/off: `on_off`
  - [x] Properties:
    - [x] Current power: `float.power`

- [x] Water heaters: `water_heater`
  - [x] Matching domain exposure:
    - [x] Default exposure: `devices.types.cooking.kettle`
  - [x] Capabilities:
    - [x] Turn on/off: `on_off`

- [x] Media players: `media_player`
  - [x] Matching domain exposure:
    - [x] Default exposure: `devices.types.media_device`
    - [x] Televisions: `devices.types.media_device.tv`
    - [x] Android TV boxes: `devices.types.media_device.tv_box`
  - [x] Capabilities:
    - [x] Input sources: `mode.input_source`
    - [x] Set/increase/decrease channel: `range.channel`
    - [x] Set/increase/decrease volume: `range.volume`
    - [x] Mute/unmute: `toggle.mute`
    - [x] Pause/unpause: `toggle.pause`

- [ ] Vacuum cleaners:
  - [x] Matching domain exposure:
    - [x] Default exposure: `devices.types.vacuum_cleaner` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-vacuum-cleaner-docpage/))
  - [ ] Capabilities _(work in progress)_


### Capabilities
- [x] On / Off: `on_off` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/on_off-docpage/))
- [ ] Color setting: `color_setting` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/))
  - [x] Temperature object: `temperature_k` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/#discovery__discovery-parameters-color-setting-table__entry__17))
  - [x] RGB palette: `color_model` -> `rgb` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/#discovery__discovery-parameters-color-setting-table__entry__17))
  - [ ] HSV palette: `color_model` -> `hsv` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/#discovery__discovery-parameters-color-setting-table__entry__17))
- [ ] Operation Mode: `mode` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-docpage/))
  - [x] Retrievable flag ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-docpage/#discovery__discovery-parameters-mode-table))
  - [ ] Cleanup mode function: `cleanup_mode` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__cleanup_mode))
  - [ ] Coffee mode function: `coffee_mode` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__coffee_mode))
  - [x] Fan speed function: `fan_speed` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__fan_speed))
  - [x] Input source function: `input_source` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__input_source))
  - [x] Program function: `program` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__program))
  - [x] Swing function: `swing` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__swing))
  - [x] Thermostat function: `thermostat` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__thermostat))
  - [ ] Work speed function: `work_speed` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__work_speed))
- [x] Range of values: `range` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-docpage/))
  - [x] Brightness function: `brightness` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__brightness))
  - [x] Channel function: `channel` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__channel))
  - [x] Humidity function: `humidity` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__humidity))
  - [x] Temperature function: `temperature` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__temperature))
  - [x] Volume function: `volume` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__volume))"
- [x] Toggle: `toggle` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-docpage/))
  - [x] Backlight function: `backlight` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__backlight))
  - [x] Controls locked function: `controls_locked` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__controls_locked))
  - [x] Ionization function: `ionization` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__ionization))
  - [x] Keep warm function: `keep_warm` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__keep_warm))
  - [x] Mute function: `mute` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__mute))
  - [x] Oscillation function: `oscillation` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__oscillation))
  - [x] Pause function: `pause` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__pause))"


### Properties
- [x] Float: `float`
  - [x] Amperage: `amperage` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/#float-instance__amperage))
    - [x] Sensors using `A` as their unit type
  - [x] CO2 level: `co2_level` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/#float-instance__co2_level))
    - [x] Air quality monitoring entities (`air_quality`)
  - [x] Humidity: `humidity` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/#float-instance__humidity))
    - [x] Sensors with `humidity` device class
    - [x] Climate entities with `current_humidity` attribute
  - [x] Power: `power` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/#float-instance__power))
    - [x] Sensors using `W` and `kW` as their unit type
  - [x] Temperature: `temperature` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/#float-instance__temperature))
    - [x] Sensors with `temperature` device class
    - [x] Climate entities with `current_temperature` attribute
  - [x] Voltage: `voltage` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/#float-instance__voltage))
    - [x] Sensors using `kV`, `mV` and `MV` as their unit type
  - [x] Water level: `water_level` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/#float-instance__water_level))
    - [x] Entities with `water_level` attribute
