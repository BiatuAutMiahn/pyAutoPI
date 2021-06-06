import serial
import time

Magic = "ftbOsM6KwAn98Y58"
Alias = "qmi"
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
    node.Serial=serial.Serial(port=config['device'],baudrate=config["baudrate"],timeout=config["timeout"])
    # node.Serial.port=config['device']
    if node.Serial.is_open:
        node.Serial.close()
    node.Serial.open()
    for c in config['init']:
        node.Serial.write((c+'\r').encode())
        time.sleep(0.1)
    logging.info("["+node.name+"]:\tInitialized")
