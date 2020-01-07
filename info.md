# Yandex Smart Home integration

## Installation
1. Update home assistant to 0.96.0 at least
1. Configure SSL certificate if it was not done already (***do not*** use self-signed certificate)
1. Create dialog via https://dialogs.yandex.ru/developer/
1. Install this component from HACS
1. Restart Home Assistant
1. Follow the example `configuration.yaml` entry below to add integration.
   1. It is also possible to enable this integration via `Settings` => `Integrations` menu within _HomeAssistant_. Search for _Yandex Smart Home_ and follow the activation wizard. Be aware that there are limitations to this method (such as current lack of per-entity configuration).
1. Add devices via your Yandex app on Android/iOS (or in _Testing_ mode).

## Example configuration
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

## Configuration variables
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
