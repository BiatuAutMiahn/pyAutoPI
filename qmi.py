import serial
import time
import pynmea2

Magic = "ftbOsM6KwAn98Y58"
Alias = "qmi"
node=None
logging=None
config = {
    'device': '/dev/ttyUSB2',
    'baudrate': 115200,
    'timeout': 1,
    'init': [
        'ATE 0',
        'AT+CMEE=1',
        'AT+QGPSCFG="autogps",1',
        'AT+QGPSCFG="fixfreq",1',
        'AT+QGPSCFG="gnssconfig",1',
        'AT+QGPSCFG="outport","usbnmea"',
        'AT+QGPSEND',
        'AT+QGPS=2,30,50,0,1'
    ]
}

def _query(c):
    node.lock=True
    node.Serial.write((c+'\r').encode())
    ret=node.Serial.readlines()
    node.lock=False
    return ret

def _show_query(c):
    ret=_query(c)
    for l in ret:
        if l==b'\r\n':
            continue
        print(l.decode())

def __init__(n,l):
    global node
    global logging
    global config
    node=n
    logging=l
    node.id=Magic
    node.config=config
    node.lock=False
    node.query=_query
    node.show_query=_show_query
    node.Serial=serial.Serial(port=config['device'],baudrate=config["baudrate"],timeout=config["timeout"])
    # node.Serial.port=config['device']
    if node.Serial.is_open:
        node.Serial.close()
    node.Serial.open()
    for c in config['init']:
        logging.info("["+node.name+"]:\tQMI <- "+c)
        ret=_query(c)
        for l in ret:
            if l==b'\r\n':
                continue
            logging.info("["+node.name+"]:\tQMI -> "+l.decode())
        #time.sleep(0.1)
    time.sleep(1)
    logging.info("["+node.name+"]:\tInitialized")
