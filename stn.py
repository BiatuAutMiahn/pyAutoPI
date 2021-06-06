Magic = "5KZMmWv2XOnD4BKD"
Alias = "stn"
node=None
logging=None

def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    logging.info("["+node.name+"]:\tInitialized")
