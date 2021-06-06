import obd

Magic = "5KZMmWv2XOnD4BKD"
Alias = "stn"
node=None
logging=None
config={'device': '/dev/serial0', 'baudrate': 9600, 'timeout': 1}

def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    node.voltage=None
    node.loop_interval=1
    node.OBD = obd.OBD(config['device'])
    logging.info("["+node.name+"]:\tInitialized")

def __loop__(self):
    node.voltage=node.OBD.query(obd.commands.ELM_VOLTAGE).value.magnitude
