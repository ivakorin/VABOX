#  boot.py from vabox
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


import gc
import json
import os
import time

import machine
import network
import ubinascii

gc.collect()
import ntptime
import micropython

gc.collect()
micropython.alloc_emergency_exception_buf(100)


def write_id():
    id = machine.unique_id()
    flashid = ubinascii.hexlify(id).decode('utf-8')
    with open('config.json') as f:
        data = json.load(f)
        data['client_id'] = str(flashid)  # TODO: Вынести к первоначальной настройке
        data['topic'] = str(flashid)  # TODO: Вынести к первоначальной настройке
    with open('config.json', 'w') as f:
        json.dump(data, f)


def update_config():
    day = list(time.localtime())
    with open('config.json') as f:
        data = json.load(f)
        data['current_date'] = ""
        data['current_day'] = day[7]
    with open('config.json', 'w') as f:
        json.dump(data, f)


def do_connect():
    # Получаем конфиг Wifi
    dir_list = os.listdir()
    if 'sunrise.json' not in dir_list:
        file = open('sunrise.json', 'w')
        file.close()
    if 'config.json' in dir_list:
        try:
            with open('config.json', 'r') as x:
                config = json.load(x)
        except ImportError:
            machine.reset()
        except ValueError:
            machine.reset()
    if 'wlanid' in config:
        wlanid = network.WLAN(network.AP_IF)
        wlanid.active(False)

    wlanid = network.WLAN(network.STA_IF)
    wlanid.active(True)
    wlanid.connect(config['wlanid'], config['wlan_password'])
    print(wlanid.ifconfig()[0])
    x = 0
    while x < 15:
        if wlanid.isconnected():
            ntptime.host = config['ntphost']
            try:
                ntptime.settime()
            except OSError:
                machine.reset()
            rtc = machine.RTC()
            tm = time.localtime(time.mktime(time.localtime()) + 5 * 3600)
            tm = tm[0:3] + (0,) + tm[3:6] + (0,)
            rtc.datetime(tm)
            break
        x += 1
        time.sleep(1)
    if config['client_id'] == '':
        write_id()
    update_config()

do_connect()
gc.collect()
