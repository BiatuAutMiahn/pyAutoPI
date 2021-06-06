Magic = "Ez18oj3rfwIZStqG"
Alias = "spm"
node=None
logging=None

def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    time.sleep(5)
    logging.info("["+node.name+"]:\tInitialized")
