from time import time

_events = []

def do_events():
    t = time()
    while _events and _events[0][0] < t:
        event = _events.pop(0)
        event[1](*event[2])


def run_in(seconds, cb, args=()):
    at = time() + seconds
    run_at(at, cb, args)


def run_at(at, cb, args=()):
    event = (at, cb, args)
    if not _events or _events[-1][0] <= at:
        _events.append(event)
        return
    
    i = len(_events) - 1
    while i != 0 and _events[i-1][0] > at:
        i -= 1
    
    _events.insert(i, event)