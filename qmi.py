Magic = "ftbOsM6KwAn98Y58"
Alias = "ec2x"
node=None
logging=None
config = {
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
}

def __init__(n,l):
    global node
    global logging
    global config
    node=n
    logging=l
    node.id=Magic
    node.config=config
    logging.info("["+node.name+"]:\tInitialized")
