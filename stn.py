import obd
import RPi.GPIO as gpio
from gpio_pin  import RPI_SHUTDN
Magic = "5KZMmWv2XOnD4BKD"
Alias = "stn"
node=None
logging=None
config={'device': '/dev/serial0', 'baudrate': 9600, 'timeout': 1}

def _query(**kwargs):
    node.lock=True
    ret=node.OBD.query(**kwargs)
    node.lock=False
    return ret

def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    node.voltage=None
    node.loop_interval=1
    gpio.setwarnings(False)
    gpio.setmode(gpio.BOARD)
    gpio.setup(RPI_SHUTDN, gpio.IN)
    node.OBD = obd.OBD(config['device'])
    node.lock=False
    node.query=_query
    logging.info("["+node.name+"]:\tInitialized")


def __deinit__(self):
    node.OBD.close()

def __loop__(self):
    try:
        if not node.lock:
            node.voltage=node.OBD.query(obd.commands.ELM_VOLTAGE).value
    except Exception as e:
        node.handle_exception(e)
