import sys
import time
from debug import log_exception
from threading import Thread, Event

def _event_thread_main(event_cb, period, exit_event):
    next_wake_time = time.time() + period
    while True:
        signaled = exit_event.wait(timeout=next_wake_time-time.time())

        if signaled:
            break

        try:
            event_cb()
        except Exception as ex:
            log_exception(ex)

        next_wake_time += period


def read_byte(event_cb, period_ms):
    exit_event = Event()
    thread = Thread(target=_event_thread_main, args=(event_cb, period_ms/1000, exit_event), daemon=True)
    thread.start()

    b = sys.stdin.buffer.read(1)[0]

    exit_event.set()
    thread.join()

    return b
