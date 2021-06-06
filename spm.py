import time
import RPi.GPIO as gpio
from gpio_pin import HOLD_PWR, SPM_RESET
from i2c_conn import I2CConn
from spm2_conn import SPM2Conn

Magic = "Ez18oj3rfwIZStqG"
Alias = "spm"
node=None
logging=None
config = {'port': 1, 'address': 8}

def reset():
    logging.info("["+node.name+"]:\tResetting SPM")
    try:
        gpio.output(HOLD_PWR, gpio.HIGH)
        gpio.output(SPM_RESET, gpio.LOW)
        time.sleep(.1)
        gpio.output(SPM_RESET, gpio.HIGH)
    finally:
        time.sleep(1)
        gpio.output(HOLD_PWR, gpio.LOW)

def __init__(n,l):
    global node
    global logging
    global wait
    global config
    node=n
    logging=l
    node.id=Magic
    node.heartbeat=0
    node.config=config
    node.SPM=SPM2Conn()
    gpio.setwarnings(False)
    gpio.setmode(gpio.BOARD)
    gpio.setup(HOLD_PWR, gpio.OUT, initial=gpio.LOW)
    gpio.setup(SPM_RESET, gpio.OUT, initial=gpio.HIGH)
    time.sleep(1)
    reset()
    time.sleep(2)
    node.SPM.init(config)
    time.sleep(8)
    logging.info("["+node.name+"]:\tInitialized")
    node.SPM.heartbeat()
    node.loop_interval=10

def __loop__(s):
    node.SPM.heartbeat()
    node.heartbeat+=1
