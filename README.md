[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)  
[![Donate](https://img.shields.io/badge/-Donate-purple.svg)](https://money.yandex.ru/to/410012369233217) _(current developer)_  
[![Donate](https://img.shields.io/badge/-Donate-purple.svg)](https://money.yandex.ru/to/41001142896898) _(original developer)_  

## Yandex Smart Home custom component for Home Assistant

## Installation
1. Update home assistant to 0.96.0 at least
1. Configure SSL certificate if it was not done already (***do not*** use self-signed certificate)
1. Create dialog via https://dialogs.yandex.ru/developer/
1. Install this component from HACS
1. Restart Home Assistant
1. Follow the example `configuration.yaml` entry below to add integration.
   1. It is also possible to enable this integration via `Settings` => `Integrations` menu within _HomeAssistant_. Search for _Yandex Smart Home_ and follow the activation wizard. Be aware that there are limitations to this method (such as current lack of per-entity configuration).
1. Add devices via your Yandex app on Android/iOS (or in _Testing_ mode).

### Configuration example
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
    switch.living_room_outlet:
      expose_as: socket
    switch.kitchen:
      name: CUSTOM_NAME_FOR_YANDEX_SMART_HOME
    light.living_room:
      room: LIVING_ROOM
      backlight: light.wall_ornament
    media_player.tv_lg:
      channel_set_via_media_content_id: true
      sources:
        one: "HDMI 1"
        two: "HDMI 2"
        three: "Composite"
        four: "Netflix App"
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
      expose_as:
          (string) (Optional) Expose this entity as something else.
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
```

### Available domains

The following domains are available to be used:

- `climate`: on/off, temperature, mode, fan speed
- `cover`: on/off (as _close/open_)
- `fan`: on/off, fan speed
- `group`: on/off
- `input_boolean`: on/off
- `scene`: on/off
- `script`: on/off
- `light`:
  - on/off
  - brightness
  - color (RGB)
  - color temperature
- `media_player`:
  - on/off
  - mute/unmute
  - volume precise setting
  - volume relative increments
  - channel precise setting (use `media_content_id` attribute as channel number, enabled in configuration)) 
  - channel relative increments (via _Previous/Next Track_ buttons or custom scrips defined in configuration)
- `switch`: on/off
- `vacuum`: on/off

### Overriding exposed entity domain &mdash; `expose_as` option

The following Yandex domains are available for overriding default exposition domain:  `light`, `socket`, `switch`, `thermostat`, `thermostat.ac`, `media_device`, `media_device.tv`,
`openable`, `openable.curtain`, `humidifier`, `purifier`, `socket`, `vacuum_cleaner` and `other`

When exposing device under a domain different from default confirm compatibility by consulting the
[Yandex API documentation](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-types-docpage/) by
comparing sets of capabilities expected from default and target domains. Very common custom exposition would
be rendering a `switch` entity (example above) as a `socket`.
 

### Room/Area support

Entities that have not got rooms explicitly set and that have been placed in Home Assistant areas will return room hints to Yandex Smart Home with the devices in those areas.

### Create Dialog

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

## Supported device types
This list is a work-in-progress registry of device types supported by this integration.  
Refer to this list as an overview of project's progress or a guide to overriding default entity exposure domains.

### Capabilities
- [x] On / Off: `on_off` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/on_off-docpage/))
- [x] Color setting: `color_setting` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/))
  - [x] Temperature object: `temperature_k` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/#discovery__discovery-parameters-color-setting-table__entry__17))
  - [x] RGB palette: `color_model` -> `rgb` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/#discovery__discovery-parameters-color-setting-table__entry__17))
  - [ ] HSV palette: `color_model` -> `hsv` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/color_setting-docpage/#discovery__discovery-parameters-color-setting-table__entry__17))
- [ ] Operation Mode: `mode` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-docpage/))
  - [x] Retrievable flag ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-docpage/#discovery__discovery-parameters-mode-table))
  - [ ] Cleanup mode function: `cleanup_mode` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__cleanup_mode))
  - [ ] Coffee mode function: `coffee_mode` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__coffee_mode))
  - [x] Fan speed function: `fan_speed` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__fan_speed))
  - [x] Input source function: `input_source` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__input_source))
  - [ ] Program function: `program` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__program))
  - [x] Swing function: `swing` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__swing))
  - [x] Thermostat function: `thermostat` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__thermostat))
  - [ ] Work speed function: `work_speed` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/#mode-instance__work_speed))"
- [ ] Range of values: `range` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-docpage/))
  - [x] Brightness function: `brightness` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__brightness))
  - [x] Channel function: `channel` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__channel))
  - [x] Humidity function: `humidity` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__humidity))
  - [x] Temperature function: `temperature` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__temperature))
  - [x] Volume function: `volume` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/#range-instance__volume))"
- [ ] Toggle: `toggle` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-docpage/))
  - [x] Backlight function: `backlight` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__backlight))
  - [ ] Controls locked function: `controls_locked` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__controls_locked))
  - [ ] Ionization function: `ionization` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__ionization))
  - [ ] Keep warm function: `keep_warm` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__keep_warm))
  - [x] Mute function: `mute` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__mute))
  - [x] Oscillation function: `oscillation` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__oscillation))
  - [x] Pause function: `pause` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/#toggle-instance__pause))"

### Domain coverage
- [x] Switch type: `devices.types.switch` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-switch-docpage/))
  - [x] Expose `switch` domain
  - [x] Expose `group` domain
  - [x] Expose `input_boolean` domain
- [x] Lights: `light` -> `devices.types.light` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-light-docpage/))
- [x] Sockets: __(???)__ -> `devices.types.socket` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-socket-docpage/))
  - [x] Full `switch` compatibility when using `entity_config.expose_as`
- [x] Thermostat: `climate` -> `devices.types.thermostat` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-thermostat-docpage/))
- [x] Air conditioner: `climate`, `fan` -> `devices.types.thermostat.ac` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-thermostat-ac-docpage/))
- [x] Media devices: `media_player` -> `devices.types.media_device` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-media-docpage/))
- [ ] Televisions: `media_player` -> `devices.types.media_device.tv` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-media-tv-docpage/))
  - [ ] Propose mainline inclusion of `device_class` attribute for `media_player` domain
  - [ ] Implement specific `device_class` checking in the _type mapper_.
- [ ] Set-top boxes: `media_player` -> `devices.types.media_device.tv_box` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-media-tv-box-docpage/))
- [ ] Receivers: `media_player` -> `devices.types.media_device.receiver` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-media-receiver-docpage/))
- [ ] Cooking appliances: __(???)__ -> `devices.types.cooking` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-cooking-docpage/))
- [ ] Coffee makers: __(???)__ -> `devices.types.cooking.coffee_maker` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-cooking-coffee-maker-docpage/))
- [ ] Kettles: __(???)__ -> `devices.types.cooking.kettle` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-cooking-kettle-docpage/))
- [ ] Generic openables: __(???)__ -> `devices.types.openable` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-openable-docpage/))
- [ ] Curtains: __(???)__ -> `devices.types.openable.curtain` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-openable-curtain-docpage/))
- [ ] Humidifiers: `climate`, `fan` -> `devices.types.humidifier` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-humidifier-docpage/))
  - [x] Expose `climate` domain
  - [x] Expose capability with certain entries from `fan` domain
  - [ ] Testing required
- [ ] Purifiers: __(???)__ -> `devices.types.purifier` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-purifier-docpage/))
- [ ] Vacuum cleaners: `vacuum` -> `devices.types.vacuum_cleaner` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-vacuum-cleaner-docpage/))
- [ ] Washing machines: __(???)__ -> `devices.types.washing_machine` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-washing-machine-docpage/))
- [x] Other: everything else -> `devices.types.other` ([docs](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-type-other-docpage/))"
