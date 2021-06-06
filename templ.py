Magic = "8hMrQ4Xq8oQl4Ecx"
Alias = "Test"
node=None
logging=None

# Called before _loop_
def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    logging.info("["+node.name+"]:\tInitialized")

# Called before node is reloaded after modification
# def __reinit(self)__

# Called before node is terminated
# def __deinit(self)__

# Called at intervals default is 0.1s
# def __loop__(self):
