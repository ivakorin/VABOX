## vabox
### Описание
Управление аквариумом на при помощи ESP32. 
#### Реализовано
+ Функция имитации рассвета и заката, на основании заданной широты и долготы со смещением в указанную временную зону. 
+ Получение температуры воды и включение/отключение охлаждающих вентиляторов.
+ Управление подачей CO2
#### В планах
+ Управление аэрацией
+ Web-интерфейс
### Схема
[Ссылка на проект в EasyEDA ](https://easyeda.com/ignat.vakorin/vabox_copy)
![Схема](/etc/Schematic_VABOX-ESP32.png "Схема")
### Запуск
1. Создать файл _config.json_
2. Внести в него: 
```
{
  "wlan_password": "", 
  "wlanid": "", 
  "ntphost": "", 
  "broker": "", 
  "mqtt_port": , 
  "mqtt_user": "", 
  "mqtt_pass": "", 
  "temp_sensor_pin": , 
  "fan_control": , 
  "client_id": "", 
  "topic": "vabox", 
  "current_date": "", 
  "lat": "", 
  "lng": "", 
  "utc_shift": , 
  "tmax": , 
  "tmin": , 
  "led_pin": , 
  "led_qty": , 
  "current_day": ,
}
```
3. Где:
```
wlan_password - пароль Wi-Fi
wlanid - имя Wi-Fi сети
ntphost - адрес NTP сервера
broker - адрес MQTT брокера
mqtt_port - порт MQTT брокера 
mqtt_user - имя пользователя MQTT  
mqtt_pass - пароль пользователя MQTT 
temp_sensor_pin - пин к которому подключён датчик температуры
fan_control - пин к которому подключён пин управления вентилятором
client_id - оставить пустым 
topic - имя MQTT топика 
current_date - оставить пустым
lat - широта
lng - долгота 
utc_shift - смещение относительно UTC (часовой пояс)
tmax - максимальная температура 
tmin - максимальная температура
led_pin - пин к которому подключены RGB-светодиоды 
led_qty - количество светодиодов в ленте 
current_day - оставить пустым
```
