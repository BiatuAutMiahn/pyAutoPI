import obd
import RPi.GPIO as gpio
from gpio_pin  import RPI_SHUTDN
import random
import string
from collections import OrderedDict

Magic = "5KZMmWv2XOnD4BKD"
Alias = "stn"
node=None
logging=None
config={'device': '/dev/serial0', 'baudrate': 9600, 'timeout': 1}

queue=None
watcher={}
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
            logging.info("["+node.name+"]:\STN -> "+c)
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
            logging.info("["+node.name+"]:\STN <- "+tmp)
    if ret_result:
        return (qid,queue[1][qid])
    return qid


def _proc_queue():
    global queue
    node.queue=queue
    for k in queue[0].copy().keys():
        # ret=node.OBD.query(k)
        queue[0][k]['stdout']=node.OBD.query(queue[0][k]['stdin'])
        queue[1][k]=queue[0].pop(k)

def __init__(n,l):
    global node
    global logging
    global config
    global queue
    node=n
    logging=l
    node.id=Magic
    node.voltage=None
    node.loop_interval=1
    node.lock=False
    node.query=_query
    node.config=config
    node.watch={'ELM_VOLTAGE':None,'ELM_VERSION':None}
    queue=[OrderedDict(),OrderedDict()]
    node.OBD = obd.OBD(node.config['device'])
    gpio.setwarnings(False)
    gpio.setmode(gpio.BOARD)
    gpio.setup(RPI_SHUTDN, gpio.IN)
    logging.info("["+node.name+"]:\tInitialized")

def __deinit__(self):
    node.OBD.close()

def __loop__(self):
    for c in node.watch.copy().keys():
        watcher[c]=_query(obd.commands[c])
    try:
        _proc_queue()
    except Exception as e:
        node.handle_exception(e)
    for c in node.watch.copy().keys():
        if watcher[c] in queue[1]:
            node.watch[c]=queue[1][watcher[c]]['stdout']
        # node.voltage=node.OBD.query(obd.commands.ELM_VOLTAGE).value
