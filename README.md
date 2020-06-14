# _Яндекс Умный Дом_ для HomeAssistant
>[![hacs_badge](https://img.shields.io/badge/HACS-Default-green.svg)](https://github.com/custom-components/hacs)
>[![Поддержка](https://img.shields.io/badge/%D0%9F%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B8%D0%B2%D0%B0%D0%B5%D1%82%D1%81%D1%8F%3F-%D0%B4%D0%B0-green.svg)](https://github.com/alryaz/hass-mosoblgaz/graphs/commit-activity)
>
>_Поддержка текущей ветки:_ @alryaz  
>[![Пожертвование Yandex](https://img.shields.io/badge/%D0%9F%D0%BE%D0%B6%D0%B5%D1%80%D1%82%D0%B2%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-Yandex-red.svg)](https://money.yandex.ru/to/410012369233217)
>[![Пожертвование PayPal](https://img.shields.io/badge/%D0%9F%D0%BE%D0%B6%D0%B5%D1%80%D1%82%D0%B2%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-Paypal-blueviolet.svg)](https://www.paypal.me/alryaz)
>
>_Оригинальный разработчик:_ @dmitry-k  
>[![Репозиторий GitHub](https://img.shields.io/badge/GitHub-dmitry--k%2Fyandex_smart_home-blue)](https://github.com/dmitry-k/yandex_smart_home)
>[![Пожертвование Yandex](https://img.shields.io/badge/%D0%9F%D0%BE%D0%B6%D0%B5%D1%80%D1%82%D0%B2%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-Yandex-red.svg)](https://money.yandex.ru/to/41001142896898)


## Установка
1. Обновите HomeAssistant до версии 0.96.0 и выше
1. Настройте SSL для HomeAssistant (***do not*** use self-signed certificate)
   1. Самоподписанные сертификаты **не подходят**
   1. Для быстрой настройки советуется использовать [Let's Encrypt](https://www.home-assistant.io/blog/2015/12/13/setup-encryption-using-lets-encrypt/)
1. Создайте диалог в [разделе разработчика диалогов Яндекс](https://dialogs.yandex.ru/developer/) (см. [детальное описание этапа](#create_dialog))
1. Установите данный компонент:
    1. _Посредством HACS: (рекомендуется)_
    	1. Найдите репозиторий `Yandex Smart Home` в поиске.  
    	   _В списке репозиториев может присутствовать оригинальная версия проекта. Для выбора данной версии, перед установкой проверьте, если @alryaz присутствует в списке разработчиков._
    	1. Установите найденную интеграцию
    1. _Ручная установка:_  
       (подразумевается: путь к конфигурации HomeAssistant = `/config`)
    	1. Клонируйте данный репозиторий:  
    	   `git clone https://github.com/alryaz/hass-component-yandex-smart-home repo`
    	1. Выберите последнюю ветку:  
    	   ``cd repo && git checkout $(git describe --tags `git rev-list --tags --max-count=1`)``
    	1. Переместите интеграцию в папку `custom_components`:  
    	   `mkdir -p /config/custom_components && mv custom_components/yandex_smart_home /config/custom_components/`
1. Перезапустите HomeAssistant
1. Следуйте одной из инструкций по настройке компонента ниже
1. Обновите устройства в приложении _Яндекс_ для [Android](https://play.google.com/store/apps/details?id=ru.yandex.searchplugin&hl=ru) / iOS (или в [панели разработчика](https://dialogs.yandex.ru/developer/) в тестовом режиме).
	1. **Не забывайте повторять последнюю операцию при добавлении новых устройств в HomeAssistant!**
	
Для работоспособности интеграции требуется произвести её настройку в два этапа. Этап для HomeAssistant
указан в данном разделе. Для перехода ко второму этапу, нажмите 

## Настройка через меню `Интеграции`
1. Откройте `Настройки` -> `Интеграции`
1. Нажмите внизу справа страницы кнопку с плюсом
1. Введите в поле поиска `Yandex Smart Home`
   1. Если по какой-то причине интеграция не была найдена, убедитесь, что HomeAssistant был перезапущен после
        установки интеграции.
1. Выберите первый результат из списка
1. Пройдите несколько этапов настройки следуя инструкциям на экране
1. Если при настройке не были допущены ошибки, интеграция будет добавлена.  
   После Вы можете перейти ко [второму этапу](#create_dialog) настройки.
   
## Настройка через `configuration.yaml`

### Базовая конфигурация
Указывается пустой новый раздел конфигруации под именем `yandex_smart_home`.  
В данном режиме **все поддерживаемые объекты** будут передаваться в Яндекс.
```yaml
# configuration.yaml
...

yandex_smart_home:
```

### Фильтр объектов
Чтобы выбрать объекты, которые следует передавать в Яндекс, задайте фильтр объектов.

Фильтр задаётся через ключ `filter` конфигурации.  
Возможные атрибуты фильтра:
  - `include_domains` &mdash; разрешить объекты из указанных доменов
  - `exclude_domains` &mdash; запретить объекты из указанных доменов _(не должно пересекаться с предыдущей опцией)_
  - `include_entities` &mdash; разрешить указанные объекты
  - `exclude_entities` &mdash; запретить указанные объекты

#### Пример конфигурации:
```yaml
yandex_smart_home:
  filter:
    # Разрешение доменов `media_player` и `switch`
    include_domains: ['media_player', 'switch']
    
    # Исключение домена `automation`
    exclude_domains: automation
    
    # Разрешение объекта `light.living_room`
    include_entities: light.living_room
    
    # Исключение объектов `switch.door_one` и `switch.door_two`
    exclude_entities:
      - switch.door_one
      - switch.door_two
```

### Расширенная конфигурация объектов
Дополнительная настройка включает в себя возможность настраивать отдельно некоторые функции и свойства объектов.
Для указания объектов и соответствующих им параметров, добавьте ключ `entity_config` в конфигурацию. 

#### Пример конфигурации
```yaml
yandex_smart_home:
  entity_config:
    ...
```
##### Объект любого домена
```yaml
    ...
    switch.kitchen:
      # Переопределение имени в Yandex
      # Определяется автоматически, по умолчанию значение атрибута `friendly_name`
      name: Кухонный выключатель

      # Переопределение комнаты в Yandex
      # Определяется автоматически, по умолчанию значение берётся из комнат в HomeAssistant
      room: Кухня
      
      # Переопределение типа устройства
      # Влияет в основном на иконку в приложении Яндекс и на интерфейс
      # взаимодействия; не влияет на автоматическое определение возможностей
      # Определяется автоматически, по умолчанию: devices.type.other
      type: devices.type.light
    ...
```
Список поддерживаемых типов для опции `type`: [Устройства - Технологии Яндекса](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/device-types-docpage/)
##### Объект домена `media_player`
```yaml
    ...
    media_player.kitchen_tv:
      # Установка канала через атрибут `media_content_id`
      # По умолчанию: false
      channel_set_via_media_content_id: true

      # Форсировать относительное изменение громкости
      # По умолчанию: false
      relative_volume_only: true

      # Указание соответствия источников значениям Яндекс
      # По умолчанию: генерируется массив соответствий первых 10 и менее источников
      # из атрибута `sources_list`.
      # Возможные ключи: one, two, three, four, five, six, seven, nine, ten
      sources:
        one: "HDMI 1"
        two: "HDMI 2"
        three: "Composite"
        four: "Netflix App"

      # Скрипт переключения на следующий канал
      # Для использования доступна переменная `entity_id`, совпадающая
      # с ключом объекта (в данном случае
      сhannel_up:
        service: custom_tv_component.next_channel
        data_template:
          entity_id: {{ entity_id }}

      # Аналогичный скрипт для переключения на предыдущий канал
      channel_down:
        service: custom_tv_component.prev_channel
        data_template:
           {{ entity_id }}
    ...
```
##### Объект домена `light`
```yaml
    ...
    light.rgb_controller:
      # (для объектов с эффектами) Указание соответствия програм значениям Яндекс
      # По умолчанию: генерируется массив соответствий первых 10 и менее эффектов
      # из атрибута `effects_list`.
      # Возможные ключи: one, two, three, four, five, six, seven, nine, ten
      programs:
        one: 0
        two: 1
        three: 2
        four: 3
```

### Расширенная конфигурация: _Переключатели (Capability &#8680; Toggle)_
Компонент поддерживает все переключатели Yandex на момент последнего обновления. Для большинства переключателей
существует процесс автоматического определения совместимости, однако в случае невозможности определить
компонентом подходящие переключатели, возможно также определить их вручную.

_Внимание:_ При наличии автоматической совместимости объекта и переключателя, и установке переопределения
посредством конфигурации, переопределение замещает собственный переключатель объекта.

Установка переопределений производится под ключом `toggles` в формате `тип: объект-переключатель`  
_Требования для объектов-переключателей:_ состояния объекта должны быть `on` или `off`  
Полный список доступных переключателей: [Список функций Toggle - Технологии Яндекса](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/toggle-instance-docpage/)

#### Пример конфигурации
```yaml
yandex_smart_home:
  entity_config:
    media_player.tv_lg:
      toggles:
        # Блокировка управления телевизором
        controls_locked: switch.custom_webostv_controls_lock
        
        # Подсветка
        backlight: light.raspberry_pi_ambilight

        # Приглушить звук
        mute: switch.sound_system
```


### Расширенная конфигурация: _Свойства (Property)_
Компонент поддерживает все свойства Yandex на момент последнего обновления. Для большинства свойств
существует процесс автоматического определения совместимости, однако в случае невозможности определить
компонентом подходящие свойства, возможно также переопределить свойства вручную.

Полный список доступных свойств: [Список свойств Float - Технологии Яндекса](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/float-instance-docpage/)  
На данный момент доступны только свойства _Float_

#### Пример конфигурации
```yaml
yandex_smart_home:
  entity_config:
    sensor.home_power_meter:
      properties:
        # Использование атрибута `voltage` объекта `sensor.home_power_meter`
        voltage: voltage

        # Использование состояния объекта `sensor.home_power_meter_current`
        current: sensor.home_power_meter_current

        # Использование атрибута `temperature` объекта `sensor.home_power_meter_temperature` 
        temperature:
          entity_id: sensor.home_power_meter_temeperature
          attribute: temperature
```

### Расширенная конфигурация: _Диапазоны (Capability -> Range)_
Для данного раздела конфигурации действуют те же регламенты, что и для _Переключателей_, за исключением того,
что целевой объект получения данных должен иметь числовое значение состояния / атрибута.

Полный список доступных диапазонов: [Список функций Range - Технологии Яндекса](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/range-instance-docpage/)

#### Пример конфигурации
```yaml
yandex_smart_home:
  entity_config:
    light.christmas_lights:
      ranges:
        # Пример: Диапазон яркости
        brightness:
          # (обязательно) Целевой объект
          entity_id: group.christmas_light_brightness

          # (обязательно) Скрипт/служба установки значения
          # При выполнении доступна переменная `value` типа `float`, содержащая
          # значение, запрошенное Яндексом, помноженное на `multiplier` (см. ниже)
          # Также доступна переменная `entity_id` с ID объекта.
          set_script:
            service: light.turn_on
            data_template:
              entity_id: {{ entity_id }}
              brightness: {{ value }}

          # Минимальное значение (для Яндекса)
          minimum: 0

          # Максимальное значение (для Яндекса)
          maximum: 100

          # Шаг изменения (в данном случае: +5, -5)
          prceision: 5

          # Множитель для значений (по умолчанию 1)
          # Требуется указывать для объектов, которые используют
          # в качестве значений дробные числа в диапазоне от 0 до 1. 
          multiplier: 0.01
          
```

### Расширенная конфигурация: _Режимы (Capability -> Mode)_
Для данного раздела конфигурации действуют те же регламенты, что и для _Переключателей_, за исключением того,
что целевой объект получения данных должен иметь состояния из списка состояний соответствующего режима,
если не указан отдельный массив соответствий между состояниями.

Полный список доступных режимов: [Список функций Mode - Технологии Яндекса](https://yandex.ru/dev/dialogs/alice/doc/smart-home/concepts/mode-instance-docpage/)

#### Пример конфигурации
```yaml
yandex_smart_home:
  entity_config:
    switch.kitchen_kettle:
      modes:
        # Пример: Режим кофемашины
        coffee_mode:
          # (обязательно) Целевой объект
          entity_id: sensor.uart_jura_coffee_mode

          # (обязательно) Скрипт/служба установки значения
          # При выполнении доступна переменная `value` типа `float`, содержащая
          # значение, запрошенное Яндексом, помноженное на `multiplier` (см. ниже).
          # Также доступна переменная `entity_id` с ID объекта.
          set_script:
            service: shell_command.send_jura_coffee_mode
            data_template:
              mode: {{ value }}

          # Сопоставление значений с объекта с доступными для режима.
          # Слева указывается режим.
          # Справа указываются все возможные состояния для соответствующего режима.
          # При установке режима, если справа задан список, будет использовано первое
          # значение из списка при вызове скрипта выше.
          mapping:
            americano: 01D3
            cappucino: ['3A12', '3A13']
            double_espresso: DD11
```

### Дополнительные параметры
```yaml
yandex_smart_home:
  # Включение диагностического режима.
  #
  # !!! !!! ВНИМАНИЕ !!! !!!
  # НЕ ИСПОЛЬЗУЙТЕ ДАННУЮ ОПЦИЮ, ЕСЛИ ВАМ ОНА НЕ ТРЕБУЕТСЯ!
  # ОНА ПОЗВОЛЯЕТ ЛЮБОЙ СЛУЖБЕ / ПОЛЬЗОВАТЕЛЮ ПОСЫЛАТЬ НА ВАШ
  # HOMEASSISTANT ЗАПРОСЫ К API КОМПОНЕНТА БЕЗ АВТОРИЗАЦИИ!
  # ДАННАЯ ФУНКЦИЯ ПРЕДНАЗНАЧЕНА ИСКЛЮЧИТЕЛЬНО ДЛЯ РАЗРАБОТКИ!
  # !!! !!! ВНИМАНИЕ !!! !!!
  #
  # По умолчанию: false
  diagnostics_mode: true

  # Скрывать уведомления с конфигурацией и предупреждения
  # о работе режима диагностики. Это полезно если Вы часто
  # перезагружаете HomeAssistant и не желаете требовать Алису
  # выполнять команду каждый раз.
  # По умолчанию: false
  hide_notifications: true
```

## Для разработчиков
Если Вы являетесь разработчиком компонента, создающего объекты, Вы можете внедрить передачу правильного
типа объекта, добавив атрибут `yandex_type` в список атрибутов состояния (`device_state_attributes`)
объекта. Это позволит улучшить связку _Устройство_ -> _HomeAssistant_ -> _Yandex_ для конечного пользователя.

## <a name="create_dialog"></a>Создание диалога

Перейдите в [панель разработчика диалгов](https://dialogs.yandex.ru/developer/) и создайте новый навык _Умный дом_:

При создании конфигурации, используйте следующие параметры

Поле | Значение
------------ | -------------
Название | Название диалога (любая строка)
Endpoint URL | `https://<Хост HomeAssistant>:<Порт>/api/yandex_smart_home`
Не показывать в каталоге | Отметить галочку
Подзаголовок | Подзаголовок (любая строка)
Имя разработчика | Ваше имя (или придуманное)
Email разработчика | Ваш E-mail в Яндекс (для подтверждения)
Официальный навык | `Нет`
Описание | Описание навыка (любая строка)
Иконка | Иконка навыка (пример: [картинка из поста](https://community.home-assistant.io/t/round-icon-for-android/23019/4))

Для связывания аккаунтов используйте кнопку внизу страницы настройки умения,
и заполните значения таким образом:

Поле | Значение
------------ | -------------
Идентификатор приложения | `https://social.yandex.net/`
Секрет приложения | Любая непустая последовательность символов
URL авторизации | `https://<Хост HomeAssistant>:<Порт>/auth/authorize`
URL для получения токена | `https://<Хост HomeAssistant>:<Порт>/auth/token`
URL для обновления токена | `https://<Хост HomeAssistant>:<Порт>/auth/token`
Идентификатор группы действий | Оставить пустым

## Поддерживаемый функционал **_(WIP)_**
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
    - [x] Switches with `socket` as device class: `devices.types.socket`
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
