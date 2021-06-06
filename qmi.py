import serial
import time
import pynmea2
import random
import string
from collections import OrderedDict

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
queue=None

def genid():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))

def _query(c,wait=False,ret_result=False,echo=False,log=False,do_proc=False):
    global queue
    global tmp
    qid=genid()
    q={'stdin':c,'stdout':None}
    if ret_result:
        wait=True
    if wait:
        if echo:
            print(c)
        if log:
            logging.info("["+node.name+"]:\tQMI -> "+c)
    queue[0][qid]=q
    if not wait:
        return qid
    while node.init==5 or node.init==4:
        if qid in queue[1]:
            break
        if do_proc:
            _proc_queue()
        time.sleep(0.1)
    if echo or log:
        tmp=""
        for l in queue[1][qid]['stdout']:
            if l==b'\r\n':
                continue
            tmp+=l.decode()
        if echo:
            print(tmp)
        if log:
            logging.info("["+node.name+"]:\tQMI <- "+tmp)
    if ret_result:
        return (qid,queue[1][qid])
    return qid


def _proc_queue():
    global queue
    node.queue=queue
    for k in queue[0].keys():
        node.Serial.write((queue[0][k]['stdin']+'\r').encode())
        queue[0][k]['stdout']=node.Serial.readlines()
        queue[1][k]=queue[0].pop(k)

def __init__(n,l):
    global node
    global logging
    global config
    global queue
    node=n
    logging=l
    node.id=Magic
    node.config=config
    node.lock=False
    node.query=_query
    node.queue=queue
    node.loop_interval=0.25
    node.gps_fix=None
    
    queue=[OrderedDict(),OrderedDict()]
    node.Serial=serial.Serial(port=config['device'],baudrate=config["baudrate"],timeout=config["timeout"])
    if node.Serial.is_open: # ensure closed before opening
        node.Serial.close()
    node.Serial.open()
    for c in config['init']:
        _query(c,wait=True,do_proc=True,log=True)
        #time.sleep(0.1)
    time.sleep(1)
    logging.info("["+node.name+"]:\tInitialized")

# Replace
def __loop__(self):
    qid=_query('AT+QGPSLOC?')
    _proc_queue()
    if qid in queue[1]:
        r=queue[1].pop(qid)
        node.gps_fix=r['stdout'][1].decode()
