Magic = "tKjCwbC624mPy2J4"
Alias = "pinger"
node=None
logging=None

def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    logging.info("["+node.name+"]:\tInitialized")
