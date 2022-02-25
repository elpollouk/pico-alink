import select
import sys

_stdin_poll = select.poll()
_stdin_poll.register(sys.stdin, select.POLLIN)

def read_byte(event_cb, period_ms):
    while True:
        ready = _stdin_poll.poll(period_ms)
        if ready:
            state = ready[0][1]
            if state != select.POLLIN:
                raise IOError(f"poll={state}")
            return sys.stdin.buffer.read(1)[0]

        event_cb()
