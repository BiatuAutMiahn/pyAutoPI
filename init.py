#!/usr/bin/python3
import decimal
import os
import time
import code
import json
import smbus
import psutil
import pickle
import pynmea2
import traceback
import datetime
import sys
import logging
import gpio_pin
from ping3 import ping
import RPi.GPIO as gpio
# from obd_conn import OBDConn
from i2c_conn import I2CConn
from spm2_conn import SPM2Conn
from serial_conn import SerialConn
#from mcp4725_conn import MCP4725Conn
import threading
print("[%s]:\t%s" % ('init', 'Importing Modules'))
#import qmilib
print("[%s]:\t%s" % ('init', 'Initializing Environment'))

config = {
    'spm': {'port': 1, 'address': 8},
    'qmi': {
        'device': '/dev/ttyUSB2',
        'baudrate': 115200,
        'timeout': 1,
        'init': [
            'AT+CMEE=0',
            'AT+QGPSCFG="autogps",1',
            'AT+QGPSCFG="fixfreq",1',
            'AT+QGPSCFG="gnssconfig",1',
            'AT+QGPSCFG="outport","usbnmea"',
            'AT+QGPSEND',
            'AT+QGPS=2,30,50,0,1'
        ]
    },
    'stn': {'device': '/dev/serial0', 'baudrate': 9600, 'timeout': 1},
    'nmea': {'device': '/dev/ttyUSB1', 'baudrate': 115200, 'timeout': 1},
    'pinger': {
        'hosts': ['8.8.8.8', '10.26.0.1', '10.26.1.1', '10.26.1.2'],
        'mean': 60,
        'online_thresh': 10,
    }
}

workers = {
    'spm': {'init': None, 'heartbeat': 0},
    'qmi': {'init': None, 'stdout': []},
    'nmea': {'init': None, 'nmea_raw': {}},
    'ping': {'init': None, 'ping_stats': {}},
    'log': {'init': None}
}
#'stn': {'init': None, 'supported_commands': {}, 'supported_protocols': {}, 'stats': {}},
threads = {}





spm = SPM2Conn()


def spm_worker():
    global workers

    def reset():
        try:
            print("[%s]:\t%s" % ('spm', 'Resetting'))
            gpio.output(gpio_pin.HOLD_PWR, gpio.HIGH)
            gpio.output(gpio_pin.SPM_RESET, gpio.LOW)
            time.sleep(.1)
            gpio.output(gpio_pin.SPM_RESET, gpio.HIGH)
        finally:
            time.sleep(1)
            gpio.output(gpio_pin.HOLD_PWR, gpio.LOW)
    try:
        print("[%s]:\t%s" % ('spm', 'Initializing'))
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(gpio_pin.HOLD_PWR, gpio.OUT, initial=gpio.LOW)
        gpio.setup(gpio_pin.SPM_RESET, gpio.OUT, initial=gpio.HIGH)
        time.sleep(1)
        reset()
        time.sleep(10)
        spm.init(config['spm'])
        # spm.restart_3v3()
        workers['spm']['init'] = 1
        print("[%s]:\t%s" % ('spm', 'Initialized'))
        print("[%s]:\t%s" % ('spm', 'Starting Heartbeat'))
    except Exception as e:
        handle_error("init.spm", e)
    while True:
        if workers['spm']['init'] == -1:
            print("[%s]:\t%s" % ('spm', 'Stopping'))
            workers['spm']['init'] = 0
            break
        try:
            spm.heartbeat()
            workers['spm']['heartbeat'] += 1
        except Exception as e:
            handle_error("worker.spm", e)
        time.sleep(1)


qmi = SerialConn()


def qmi_worker():
    global workers
    if workers['qmi']['init'] == -2:
        return
    try:
        print("[%s]:\t%s" % ('qmi', 'Waiting for spm'))
        while workers['spm']['init'] != 1:
            time.sleep(1)
            continue
        print("[%s]:\t%s" % ('qmi', 'Initializing'))
        qmi.init(config['qmi'])
        for c in config['qmi']['init']:
            qmi.write_line(c.encode())
            time.sleep(0.1)
        time.sleep(1)
        workers['qmi']['init'] = 1
        print("[%s]:\t%s" % ('qmi', 'Initialized'))
    except Exception as e:
        handle_error("init.qmi", e)
    while True:
        if workers['qmi']['init'] == -1:
            print("[%s]:\t%s" % ('qmi', 'Stopping'))
            workers['qmi']['init'] = 0
            break
        try:
            if not qmi.is_open():
                time.sleep(1)
                continue
            # for l in qmi.read_lines():
            #     workers['qmi']['stdout']
        except Exception as e:
            handle_error("worker.qmi", e)
        time.sleep(1)


nmea = SerialConn()


def nmea_worker():
    global workers
    global qmi

    def obj_as_dict(obj, check=True, verbose=False):
        ret = {}

        for f in obj.fields:
            desc = f[0]
            attr = f[1]
            val = getattr(obj, attr)

            if not val and not verbose:
                continue

            # Workaround because msgpack will not serialize datetime.date, datetime.time and decimal.Decimal
            if isinstance(val, datetime.date):
                val = str(val)
            elif isinstance(val, datetime.time):
                val = str(val)
            elif isinstance(val, decimal.Decimal):
                val = float(val)
            # TODO: Temp fix to get correct types because pynmea2 does not handle it
            elif attr.startswith("num_") or attr.endswith("_num") or "_num_" in attr:
                val = int(val)
            elif attr.startswith("snr_") or attr.startswith("azimuth_"):
                val = float(val)

            ret[attr] = val if not verbose else {
                "description": desc,
                "value": val
            }

        return ret

    def RMC_to_dict(c):
        ret = {}
        ret['timestamp'] = datetime.datetime.combine(
            c.datestamp, c.timestamp).isoformat()
        ret['status'] = c.status
        ret['lat'] = c.latitude
        ret['lat_dir'] = c.lat_dir
        ret['lon'] = c.longitude
        ret['lon_dir'] = c.lon_dir
        ret['spd_over_grnd'] = c.spd_over_grnd
        ret['true_course'] = c.true_course
        ret['mag_variation'] = c.mag_variation
        ret['mag_var_dir'] = c.mag_var_dir
        return ret
    try:
        print("[%s]:\t%s" % ('nmea', 'Waiting for qmi'))
        while workers['qmi']['init'] != 1:
            time.sleep(1)
            continue
        print("[%s]:\t%s" % ('nmea', 'Initializing'))
        nmea.init(config['nmea'])
        nmea.open()
        time.sleep(1)
        workers['nmea']['init'] = 1
        print("[%s]:\t%s" % ('nmea', 'Initialized'))
        print("[%s]:\t%s" % ('nmea', 'Starting NMEA Logging'))
    except Exception as e:
        handle_error("init.nmea", e)
    while True:
        if workers['nmea']['init'] == -1:
            print("[%s]:\t%s" % ('nmea', 'Stopping'))
            workers['nmea']['init'] = 0
            break
        try:
            if not nmea.is_open():
                time.sleep(1)
                continue
            lines = nmea.read_lines()
            if lines is None:
                time.sleep(1)
                continue
            for l in lines:
                o = pynmea2.parse(l.decode(), check=True)
                n = o.__class__.__name__
                if n == 'RMC':
                    o = RMC_to_dict(o)
                else:
                    o = obj_as_dict(o)
                if not n in workers['nmea']['nmea_raw']:
                    workers['nmea']['nmea_raw'][n] = []
                workers['nmea']['nmea_raw'][n].append(o)
        except Exception as e:
            handle_error("worker.nmea", e)
        time.sleep(1)


def ping_worker():
    global workers
    avg = {}
    workers['ping']['init'] = 1
    print("[%s]:\t%s" % ('ping', 'Starting Pinger'))
    while True:
        if workers['ping']['init'] == -1:
            print("[%s]:\t%s" % ('ping', 'Stopping Pinger'))
            workers['ping']['init'] = 0
            break
        try:
            for h in config['pinger']['hosts']:
                if not h in workers['ping']['ping_stats']:
                    avg[h] = [0] * (config['pinger']['mean']+2)
                    workers['ping']['ping_stats'][h] = {
                        'lat': None, 'avg': 0, 'up': 0, 'down': 0, 'up_total': 0, 'down_total': 0, 'online': False}
                    avg[h][0] = 0
                    avg[h][1] = 2
                workers['ping']['ping_stats'][h]['lat'] = ping(
                    h, timeout=1, unit='ms')
                if avg[h][0] < config['pinger']['mean']:
                    avg[h][0] += 1
                if workers['ping']['ping_stats'][h]['lat'] != None:
                    avg[h][avg[h][1]] = workers['ping']['ping_stats'][h]['lat']
                else:
                    avg[h][avg[h][1]] = 0
                workers['ping']['ping_stats'][h]['avg'] = sum(
                    avg[h][2:len(avg[h])+1])/avg[h][0]
                avg[h][1] += 1
                if avg[h][1] > config['pinger']['mean']:
                    avg[h][1] = 2
                if workers['ping']['ping_stats'][h]['lat'] != None:
                    workers['ping']['ping_stats'][h]['up'] += 1
                    workers['ping']['ping_stats'][h]['up_total'] += 1
                    workers['ping']['ping_stats'][h]['down'] = 0
                else:
                    workers['ping']['ping_stats'][h]['up'] = 0
                    workers['ping']['ping_stats'][h]['down'] += 1
                    workers['ping']['ping_stats'][h]['down_total'] += 1
                if workers['ping']['ping_stats'][h]['up']-workers['ping']['ping_stats'][h]['down'] > config['pinger']['online_thresh']:
                    workers['ping']['ping_stats'][h]['online'] = True
                else:
                    workers['ping']['ping_stats'][h]['online'] = False
                    avg[h] = [0] * (config['pinger']['mean']+2)
                    avg[h][0] = 0
                    avg[h][1] = 2
        except Exception as e:
            handle_error("worker.ping", e)
        time.sleep(1)


def log_worker():
    global workers
    old_log = {}
    try:
        print("[%s]:\t%s" % ('ping', 'Starting Logger'))
        workers['log']['init'] = 1
    except Exception as e:
        handle_error("init.log", e)
    while True:
        if workers['log']['init'] == -1:
            print("[%s]:\t%s" % ('ping', 'Stopping Logger'))
            workers['log']['init'] = 0
            break
        try:
            with open('/nfsroot/autopi_nmea.dat', 'rb') as f:
                old_log = pickle.load(f)
        except Exception as e:
            handle_error("worker.log", e)
        try:
            old_log.update(workers['nmea']['nmea_raw'])
            with open('/nfsroot/autopi_nmea.dat', 'wb') as f:
                pickle.dump(old_log, f)
            pass
        except Exception as e:
            handle_error("worker.log", e)
        time.sleep(10)


#     def stn_ensure_open(is_open):
#         if is_open:
#             # Check if the STN is powered off/sleeping (might be due to low battery)
#             if gpio.input(22) != False:
#                 #log.warn("Closing OBD connection permanently because the STN has powered off")
#                 state['stn']['device'].close(permanent=True)
#                 # raise Warning("OBD connection closed permanently because the STN has powered off")

#stn = OBDConn()


def stn_worker():
    global workers
    try:
        print("[%s]:\t%s" % ('stn', 'Initializing'))
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(22, gpio.IN)
        stn.setup(protocol={}, device=config['stn']['device'],
                  baudrate=config['stn']['baudrate'], timeout=config['stn']['timeout'])
        stn.reset()
        stn.reset()
        time.sleep(1)
        for x in stn.supported_commands():
            workers['stn']['supported_commands'][x.name] = x
        workers['stn']['init'] = 1
        print("[%s]:\t%s" % ('stn', 'Initializing'))
        print("[%s]:\t%s" % ('stn', 'Starting OBD Watcher'))
    except Exception as e:
        handle_error("init.stn", e)
    while True:
        if workers['stn']['init'] == -1:
            print("[%s]:\t%s" % ('stn', 'Stopping'))
            workers['stn']['init'] = 0
            break
        try:
            if 'ELM_VOLTAGE' in workers['stn']['supported_commands'].keys():
                workers['stn']['stats']['ELM_VOLTAGE'] = stn.query(
                    workers['stn']['supported_commands']['ELM_VOLTAGE']).value
        except Exception as e:
            handle_error("workers.stn", e)
        time.sleep(1)


print("[%s]:\t%s" % ('init', 'Setting Priority'))
psutil.Process(os.getpid()).nice(-2)
print("[%s]:\t%s" % ('init', 'Initializing GPIOs'))
gpio.setwarnings(False)
gpio.setmode(gpio.BOARD)
print("[%s]:\t%s" % ('init', 'Initializing LEDs'))
gpio.setup(gpio_pin.LED, gpio.OUT)
led_pwm = None
led_pwm = gpio.PWM(gpio_pin.LED, 15)
led_pwm.start(0)


def init_worker(w):
    threads[w] = threading.Thread(
        target=globals()[w+'_worker'], args=())
    print("[%s]:\tStarting %s worker" % ('init', w))
    threads[w].start()


for w in workers.keys():
    init_worker(w)
time.sleep(2)
led_pwm.ChangeFrequency(2)
led_pwm.ChangeDutyCycle(50)
print("[Init]:\tSystem Ready")
code.interact(local=dict(globals(), **locals()))
for w in workers.keys():
    print("[%s]:\t%s" % ('deinit', w))
    workers[w]['init'] = -1
    print("[%s]:\t%s" % ('deinit.thread.join', w))
    threads[w].join()
exit()
