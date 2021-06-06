import threading
import logging
import importlib
import code
import time
import random
import string
import traceback
import os
import sys
import readline
import rlcompleter
import atexit
def genid():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
class Node(threading.Thread):
    def __init__(self,name):
        threading.Thread.__init__(self)
        self.init = 3
        self.log = []
        self.id = None
        self.module = None
        self.mtime = None
        self.status = None
        self.exception = None
        self.name = name
    def handle_exception(self,e):
        global logging
        self.status="Exception"
        self.exception="".join(traceback.TracebackException.from_exception(e).format())
        logging.info("[%s]:\tNode encountered an Exception"%self.name)
        self.init=1
    def suspend(self):
        global logging
        self.status="Suspended"
        logging.info("[%s]:\tNode has been suspended"%self.name)
        self.init=2
    def terminate(self):
        self.init=0
    def reload(self):
        self.init=3
    def interact(self):
        global logging
        ps1=sys.ps1
        sys.ps1=self.name+'> '
        vars=dict(globals(), **locals())
        readline.set_completer(rlcompleter.Completer(vars).complete)
        readline.parse_and_bind("tab:complete")
        code.interact(local=vars,banner='')
        sys.ps1=ps1
    def run(self):
        global logging
        while True:
            if self.init==0:
                self.status="Terminating"
                logging.info("[%s]:\tNode is shutting down"%self.name)
                if hasattr(self.module,'__deinit__'):
                    self.module.__deinit__()
                else:
                    logging.warning("[%s]:\tNode has no __deinit__ method"%self.name)
                del self.module
                self.module=None
                break
            elif self.init in [1,2]:
                time.sleep(0.1)
                continue
            elif self.init==3:
                try:
                    self.status="Loading"
                    logging.info("[%s]:\tLoading Module"%self.name)
                    if self.module!=None:
                        self.status="Reloading"
                        if hasattr(self.module,'__reinit__'):
                            self.module.__reinit__(self)
                        else:
                            logging.warning("[%s]:\tNode has no __reinit__ method"%self.name)
                        logging.info("[%s]:\tReloading Module"%self.name)
                        importlib.reload(self.module)
                    else:
                        if hasattr(self.module,'__reg__'):
                            self.status="Registering"
                            self.module.__reg__(self)
                        else:
                            logging.warning("[%s]:\tNode has no __reg__ method"%self.name)
                    self.module = __import__(self.name)
                    self.mtime=os.stat(self.module.__file__).st_mtime
                    self.init=4
                except Exception as e:
                    self.handle_exception(e)
            elif self.init==4:
                try:
                    if not hasattr(self.module,'__init__'):
                        logging.error("[%s]:\tNode has no __init__ method"%self.name)
                        self.status="Exception"
                        self.exception="No __init__ method!"
                        self.init=0
                        del self.module
                        self.module=None
                        break
                    self.status="Initializing"
                    logging.info("[%s]:\tInitializing Node"%self.name)
                    self.module.__init__(self,logging)
                    self.init=5
                    if not hasattr(self.module,'__loop__'):
                        logging.warning("[%s]:\tNode has no __loop__ method"%self.name)
                except Exception as e:
                    self.handle_exception(e)
                pass
            elif self.init==5:
                try:
                    self.status="Running"
                    if hasattr(self.module,'__loop__'):
                        self.module.__loop__(self)
                except Exception as e:
                    self.handle_exception(e)
                pass
            if self.module and self.init==1 or self.init==5:
                mtime=os.stat(self.module.__file__).st_mtime
                if mtime!=self.mtime:
                    self.mtime=mtime
                    self.init=3
            time.sleep(0.1)
        self.status="Terminated"
        logging.info("[%s]:\tNode has been Terminated"%self.name)
def exit():
        logging.info("[root]:\tTerminating Nodes")
        for m in modules.keys():
            modules[m].terminate()
        for m in modules.keys():
            modules[m].join()
        sys.exit()
logging.basicConfig(format='[%(asctime)s.%(msecs)03d]%(message)s',level=logging.INFO,datefmt="%Y.%m.%d,%H:%M:%S")
logging.info("[root]:\tInitializing")
modules={'templ': None,'spm': None,'ec2x': None,'stn': None}
atexit.register(exit)
for m in modules.keys():
    modules[m]=Node(m)
    modules[m].start()
    globals()[m]=modules[m]
sys.ps1='root> '
vars = globals()
vars.update(locals())
readline.set_completer(rlcompleter.Completer(vars).complete)
readline.parse_and_bind("tab: complete")
logging.info("[root]:\tStarting Console")
while modules['spm'].init!=5:
    time.sleep(1)
time.sleep(2)
code.interact(local=vars)
exit()
# code.interact(local=dict(globals(), **locals()))
