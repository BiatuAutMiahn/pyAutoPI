Magic = "9TW543hmzbbBQXKL"
Alias = "www"
node=None
logging=None

def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    logging.info("["+node.name+"]:\tInitialized")
