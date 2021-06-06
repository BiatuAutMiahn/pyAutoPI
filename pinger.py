from ping3 import ping
import json

Magic = "tKjCwbC624mPy2J4"
Alias = "pinger"
node=None
logging=None

config={
    'hosts': ['8.8.8.8', '10.26.0.1', '10.26.1.1', '10.26.1.2'],
    'mean': 60,
    'online_thresh': 10,
}

avg = {}

def _show_stats():
    print(json.dumps(node.ping_stats,indent=4))

def __init__(n,l):
    global node
    global logging
    global config
    node=n
    logging=l
    node.id=Magic
    node.loop_interval=1
    node.ping_stats={}
    node.config=config
    node.show_stats=_show_stats
    logging.info("["+node.name+"]:\tInitialized")


def __loop__(self):
    for h in config['hosts']:
        if not h in node.ping_stats:
            avg[h] = [0] * (config['mean']+2)
            node.ping_stats[h] = {
                'lat': None, 'avg': 0, 'up': 0, 'down': 0, 'up_total': 0, 'down_total': 0, 'online': False}
            avg[h][0] = 0
            avg[h][1] = 2
        node.ping_stats[h]['lat'] = ping(
            h, timeout=1, unit='ms')
        if avg[h][0] < config['mean']:
            avg[h][0] += 1
        if node.ping_stats[h]['lat'] != None:
            avg[h][avg[h][1]] = node.ping_stats[h]['lat']
        else:
            avg[h][avg[h][1]] = 0
        node.ping_stats[h]['avg'] = sum(
            avg[h][2:len(avg[h])+1])/avg[h][0]
        avg[h][1] += 1
        if avg[h][1] > config['mean']:
            avg[h][1] = 2
        if node.ping_stats[h]['lat'] != None:
            node.ping_stats[h]['up'] += 1
            node.ping_stats[h]['up_total'] += 1
            node.ping_stats[h]['down'] = 0
        else:
            node.ping_stats[h]['up'] = 0
            node.ping_stats[h]['down'] += 1
            node.ping_stats[h]['down_total'] += 1
        if node.ping_stats[h]['up']-node.ping_stats[h]['down'] > config['online_thresh']:
            node.ping_stats[h]['online'] = True
        else:
            node.ping_stats[h]['online'] = False
            avg[h] = [0] * (config['mean']+2)
            avg[h][0] = 0
            avg[h][1] = 2
