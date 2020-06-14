# HomeAssistant Hekr Devices Integration
[![GitHub Page](https://img.shields.io/badge/GitHub-alryaz%2Fhass--component--yandex--smart--home-blue)](https://github.com/alryaz/hass-component-yandex-smart-home)
[![Donate Yandex](https://img.shields.io/badge/Donate-Yandex-red.svg)](https://money.yandex.ru/to/410012369233217)
[![Donate PayPal](https://img.shields.io/badge/Donate-Paypal-blueviolet.svg)](https://www.paypal.me/alryaz)
{% set mainline_num_ver = version_available.replace("v", "").replace(".", "") | int %}{%- set features = {
    'v2.0.0': 'Стандартный релиз; переопределения умений и свойств; настройка на русском',
}-%}{%- set breaking_changes = namespace(header=True, changes={}) -%}{%- set bug_fixes = namespace(header=True, changes={}) -%}

{% if installed %}{% if version_installed == "master" %}
#### ⚠ Вы используете версию для разработчиков
Эта ветка может оказаться нестабильной, так как содержит изменения, которые не всегда протестированы.  
Пожалуйста, не используйте данную ветку для развёртывания в боевой среде.
{% else %}{% set num_ver = version_installed.replace("v", "").replace(".","") | int %}{% if version_installed == version_available %}
#### ✔ Вы используете последнюю версию{% else %}
#### 🚨 Вы используете устаревшую версию{% if num_ver < 20 %}

{% for ver, changes in breaking_changes.changes.items() %}{% set ver = ver.replace("v", "").replace(".","") | int %}{% if num_ver < ver %}{% if breaking_changes.header %}
##### Критические изменения (`{{ version_installed }}` -> `{{ version_available }}`){% set breaking_changes.header = False %}{% endif %}{% for change in changes %}
{{ '- '+change }}{% endfor %}{% endif %}{% endfor %}
{% endif %}{% endif %}

{% for ver, fixes in bug_fixes.changes.items() %}{% set ver = ver.replace("v", "").replace(".","") | int %}{% if num_ver < ver %}{% if bug_fixes.header %}
##### Исправления (`{{ version_installed }}` -> `{{ version_available }}`){% set bug_fixes.header = False %}{% endif %}{% for fix in fixes %}
{{ '- ' + fix }}{% endfor %}{% endif %}{% endfor %}

## Возможности{% for ver, text in features.items() %}{% set feature_ver = ver.replace("v", "").replace(".", "") | int %}
- {% if num_ver < feature_ver %}**{% endif %}`{{ ver }}` {% if num_ver < feature_ver %}NEW** {% endif %}{{ text }}{% endfor %}

Пожалуйста, сообщайте об ошибках [в репозиторий GitHub](https://github.com/alryaz/hass-component-yandex-smart-home/issues).
{% endif %}{% else %}
## Возможности{% for ver, text in features.items() %}
- {{ text }} _(supported since `{{ ver }}`)_{% endfor %}
{% endif %}

## Установка
1. Обновите HomeAssistant до версии 0.96.0 и выше
1. Настройте SSL для HomeAssistant (***do not*** use self-signed certificate)
   1. Самоподписанные сертификаты **не подходят**
   1. Для быстрой настройки советуется использовать [Let's Encrypt](https://www.home-assistant.io/blog/2015/12/13/setup-encryption-using-lets-encrypt/)
1. Создайте диалог в [разделе разработчика диалогов Яндекс](https://dialogs.yandex.ru/developer/) (см. [детальное описание этапа](#create_dialog))
1. Установите данный компонент
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
Перейдите в [панель разработчика диалогов](https://dialogs.yandex.ru/developer/) и создайте новый навык _Умный дом_:

[<img alt="Панель разработчика диалогов" src="https://raw.githubusercontent.com/alryaz/hass-component-yandex-smart-home/master/images/step_developer_page.png" height="200">](https://raw.githubusercontent.com/alryaz/hass-component-yandex-smart-home/master/images/step_developer_page.png)
[<img alt="Выбор типа умения" src="https://raw.githubusercontent.com/alryaz/hass-component-yandex-smart-home/master/images/step_developer_type.png" height="200">](https://raw.githubusercontent.com/alryaz/hass-component-yandex-smart-home/master/images/step_developer_type.png)

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