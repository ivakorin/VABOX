#  main.py from vabox
#  Copyright (C) 2020  Ignat Vakorin
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#


import gc
import json
import time

import ds18x20
import machine
import neopixel
import ntptime
import onewire
import urequests
from machine import Timer
from umqtt.simple import MQTTClient

''' Цвет диодов по таблице http://www.vendian.org/mncharity/dir3/blackbody/UnstableURLs/bbr_color.html CIE 1964 10 degree CMFs'''
light_color_list = ((255, 109, 0),
                    (255, 115, 0),
                    (255, 121, 0),
                    (255, 126, 0),
                    (255, 131, 0),
                    (255, 137, 18),
                    (255, 142, 33),
                    (255, 147, 44),
                    (255, 152, 54),
                    (255, 157, 63),
                    (255, 161, 72),
                    (255, 165, 79),
                    (255, 169, 87),
                    (255, 173, 94),
                    (255, 177, 101),
                    (255, 180, 107),
                    (255, 184, 114),
                    (255, 187, 120),
                    (255, 190, 126),
                    (255, 193, 132),
                    (255, 196, 137),
                    (255, 199, 143),
                    (255, 201, 148),
                    (255, 204, 153),
                    (255, 206, 159),
                    (255, 209, 163),
                    (255, 211, 168),
                    (255, 213, 173),
                    (255, 215, 177),
                    (255, 217, 182),
                    (255, 219, 186),
                    (255, 221, 190),
                    (255, 223, 194),
                    (255, 225, 198),
                    (255, 227, 202),
                    (255, 228, 206),
                    (255, 230, 210),
                    (255, 232, 213),
                    (255, 233, 217),
                    (255, 235, 220))

'''Функция чтения конфигов, в зависимости от вида запроса либо конфиг устройства, либо данные по рассвету/закату'''


def get_config(data):
    try:
        with open(data + '.json', 'r') as x:
            response = json.load(x)
        return response
    except OSError:
        print('OSError, go to reset')
        # time.sleep_ms(2000)
        # machine.reset()
    except ImportError:
        print('ImportError, go to reset')
        machine.reset()
        time.sleep_ms(2000)
    except ValueError:
        if data == 'sunrise':
            get_json()
            with open(data + '.json', 'r') as x:
                response = json.load(x)
            return response
        else:
            print('ValueError, go to reset')
            time.sleep_ms(2000)
            machine.reset()


'''Получаем данные по рассвету/закату'''


def get_json():
    today_list = list(time.localtime())
    today = str(today_list[0]) + "-" + str(today_list[1]) + "-" + str(today_list[2])
    config = get_config('config')
    if config == None:
        return False
    else:
        try:
            r = urequests.get("https://api.sunrise-sunset.org/json?lat=" + config['lat'] + "&lng=" + config[
                'lng'] + "&date=" + today + "&formatted=0").text
            sunrise_json = json.loads(r)
            with open("sunrise.json", "w") as write_file:
                json.dump(sunrise_json, write_file)
            return True
        except OSError:
            return False


'''Получаем время рассвета'''


def set_sunrise(data):
    file = get_config('sunrise')
    request = data
    if file is False:
        responce = list(time.localtime())
        responce[3] = 9
        responce[4] = 0
        responce[5] = 0
    else:
        s = file['results'][request]
        s = s.replace('+00:00', ',0')
        s = s.replace(':', ',')
        s = s.replace('-', ',')
        s = s.replace('T', ',')
        responce = s.split(',')
        responce = list(map(int, responce))
        t = time.localtime()
        wd = t[6]
        yd = t[7]
        responce[-1] = wd
        responce.append(yd)
    return responce


'''Получаем длинну дня'''


def set_day_length():
    data_source = get_config('sunrise')
    if data_source is False:  # Если вдруг не удалось прочитать JSON
        data = 43200000
    else:
        data = data_source['results']['day_length']
        data = data * 1000  # Переводим в миллисекунды для RTC
    return data


'''Функция для корректировки времени на ESP'''


def time_correct():
    config = get_config('config')
    ntptime.host = config['ntphost']
    ntptime.settime()
    rtc = machine.RTC()
    tm = time.localtime(time.mktime(time.localtime()) + config['utc_shift'] * 3600)
    tm = tm[0:3] + (0,) + tm[3:6] + (0,)
    rtc.datetime(tm)
    update_config()


'''В случае если был сбой по питанию и контроллёр перезагрузился в середние дня'''


def half_day_sun(count):
    parts = (len(light_color_list) - 1) // 2
    day_length = set_day_length()
    sleep = day_length // len(light_color_list)
    if count < 0:
        half_day = len(light_color_list) // 2
        count = half_day - abs(count)
        i = count
        while i > 0:
            led(light_color_list[i])
            i -= 1
            time.sleep_ms(sleep)
        sunset(i, sleep)
    else:
        i = count
        while i < parts + 1:
            led(light_color_list[i])
            i += 1
            time.sleep_ms(sleep)
        sunset(i, sleep)


'''Расчёт текущего света'''


def half_day_calculate(now, first):
    part = set_day_length() // len(light_color_list)
    sec = count_secs(now, first)
    half_day = len(light_color_list) // 2
    now = sec // part
    if now > half_day:
        count = half_day - now
        print('Half day calculated, now is:' + str(count) + '. Try to start...')
        half_day_sun(count)
    else:
        print('Half day calculated, now is:' + str(now) + '. Try to start...')
        half_day_sun(now)


'''Рассвет'''


def sunrise():
    timers('deinit', 1)
    today = list(time.localtime())
    curr_day = today[7]
    with open('config.json') as f:
        data = json.load(f)
        data['current_day'] = curr_day
    with open('config.json', 'w') as f:
        json.dump(data, f)
    first = set_sunrise('sunrise')
    second = set_sunrise('astronomical_twilight_begin')
    sec = count_secs(first, second)
    parts = (len(light_color_list) - 1) // 2
    print('Start sun emulation')
    sun_emulation('sunrise', sec)
    print('Start day')
    i = 0
    day_length = set_day_length()
    sleep = (day_length - sec) // len(light_color_list)
    while i < parts + 1:
        led(light_color_list[i])
        i += 1
        time.sleep_ms(sleep)
    print('Try start sunset')
    sunset(i, sleep)


'''Закат'''


def sunset(count, timer):
    i = count
    tuple_len = len(light_color_list)
    if i > tuple_len:
        now = today_list('')
        secs = count_secs(now, False)
        count = 86400000 - secs
        print("Sunset was done, start new day timer")
        timers('day_end', count)
        return 'Cancelled'
    sleep = timer
    while i > 0:
        led(light_color_list[i])
        i -= 1
        time.sleep_ms(sleep)
    first = set_sunrise('astronomical_twilight_end')
    second = set_sunrise('sunset')
    sec = count_secs(first, second)
    print('Try sunset emulation')
    sun_emulation('sunset', sec)
    print('start light mgmnt')
    light_mgmnt()


'''Имитируем рассвет или закат'''


def sun_emulation(data, sec):
    rgb = light_color_list[0]
    start = 1
    finish = 101
    step = 1
    msec = sec // (finish // step)
    print('Sleep:' + str(msec / 1000))
    if data == 'sunrise':
        for x in reversed(range(start, finish, step)):  # Колхоз, чтобы не было деления на 0 и кол-во шагов сохранилось
            R = round(rgb[0] // x)
            G = round(rgb[1] // x)
            B = round(rgb[2] // x)
            led((R, G, B))
            time.sleep_ms(msec)
        return True
    else:
        for x in (range(start, finish, step)):  # Колхоз, чтобы не было деления на 0 и кол-во шагов сохранилось
            R = round(rgb[0] // x)
            G = round(rgb[1] // x)
            B = round(rgb[2] // x)
            led((R, G, B))
            time.sleep_ms(msec)
        led((0, 0, 0))
        return True


'''Рассчитываем микросикунды, используется в функции управления светом'''


def count_secs(first, second):
    first_sec = list()
    if second is False:
        for i in first[3:6]:
            first_sec.append(i)
        sec = sum(x * int(t) for x, t in zip([3600, 60, 1], first_sec)) * 1000
        return sec
    else:
        second_sec = list()
        f = 3
        for i in first[3:6]:
            first_sec.append(i)
            second_sec.append(second[f])
            f += 1
        sec = (sum(x * int(t) for x, t in zip([3600, 60, 1], first_sec)) - sum(
            x * int(t) for x, t in zip([3600, 60, 1], second_sec))) * 1000
        return sec


'''Получаем текущий день'''


def today_list(data):
    today_list = list(time.localtime())
    if data == 'day':  # Если нужен только номер дня
        return today_list[7]
    else:
        return today_list


''' Датчик температуры и вентилятор '''


def fan(state):
    config = get_config('config')
    fan_control = config['fan_control']
    fan = machine.Pin(fan_control, machine.Pin.OUT, value=0)
    fan.value(state)
    if state == 1:
        mqtt('fan', 'on')
    else:
        mqtt('fan', 'off')
    time.sleep_ms(2000)


def temp_sensor():
    config = get_config('config')
    tmax = config['tmax']
    tmin = config['tmin']
    temp_sensor_pin = config['temp_sensor_pin']
    dat = machine.Pin(temp_sensor_pin)
    ds = ds18x20.DS18X20(onewire.OneWire(dat))
    ds.convert_temp()
    roms = ds.scan()
    for rom in roms:
        temp = ds.read_temp(rom)
    if temp > tmax:
        fan(1)
    elif temp <= tmin:
        fan(0)
    mqtt('temp_sensor', str(temp))


'''MQTT'''


def mqtt(topic, data):
    config = get_config('config')
    client = MQTTClient(client_id=config['client_id'], server=config['broker'], port=config['mqtt_port'],
                        user=config['mqtt_user'], password=config['mqtt_pass'])
    client.connect()
    try:
        client.publish('vabox/' + config['client_id'] + '/' + topic, str(data))
        client.disconnect()
    except OSError:
        pass


'''Управление светодиодной лентой'''


def led(rgb):
    config = get_config('config')
    led_pin = config['led_pin']
    led_qty = config['led_qty']
    np = neopixel.NeoPixel(machine.Pin(led_pin), led_qty)
    np.fill(rgb)
    np.write()
    temp_sensor()
    print(str(rgb))


'''Основная функция для управления светом'''


def light_mgmnt():
    gc.collect()
    '''Стартуем таймер для публикации в MQTT'''
    publish_timer()
    config = get_config('config')
    conf_day = config['current_day']
    today = list(time.localtime())
    curr_day = today[7]
    sunrise = set_sunrise('astronomical_twilight_begin')
    sunset = set_sunrise('sunset')
    now = today_list('')
    if now[2] > sunrise[2] or curr_day > conf_day:
        time_correct()
        get_json()
        get_config('sunrise')
        light_mgmnt()
    elif sunrise < now < sunset:
        print('Half day')
        half_day_calculate(now, sunrise)
    elif now[3] < sunrise[3]:
        get_json()
        get_config('sunrise')
        timer = count_secs(sunrise, now)
        print('now < sunrise')
        timers('sunrise', timer)
    else:
        current_sec = count_secs(now, False)
        timer = 86400000 - current_sec + 100
        print('Timer to end day')
        timers('day_end', timer)


def timers(tipe, arg):
    timer = Timer(-1)
    if tipe == 'sunrise':
        print('count to sunrise: ' + str(arg))
        timer.init(period=arg, mode=Timer.ONE_SHOT, callback=lambda t: sunrise())
    elif tipe == 'day_end':
        print('count to end of day is: ' + str(arg))
        timer.init(period=arg + 18000000, mode=Timer.ONE_SHOT, callback=lambda t: light_mgmnt())
    elif tipe == 'deinit':
        timer.deinit()
    # timer.init(period=120000, mode=Timer.PERIODIC, callback=lambda t:temp_sensor())
    # timer.deinit()


def publish_timer():
    timer = Timer(-2)
    timer.init(period=120000, mode=Timer.PERIODIC, callback=lambda t: temp_sensor())


temp_sensor()
light_mgmnt()
