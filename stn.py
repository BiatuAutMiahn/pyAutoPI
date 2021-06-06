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
    node.OBD = obd.OBD(config['device'])
    logging.info("["+node.name+"]:\tInitialized")
