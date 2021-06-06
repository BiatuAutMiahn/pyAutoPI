import time

# class Node(object):
Magic = "ftbOsM6KwAn98Y58"
Alias = "ec2x"
node=None
logging=None

def __init__(n,l):
    global node
    global logging
    node=n
    logging=l
    node.id=Magic
    logging.info("["+node.name+"]:\tInitialized")
