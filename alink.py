from sys import stdin, implementation
# pyright: reportMissingImports=false

import config
import log
import memlog

log.log("Starting...")

IS_MICROPYTHON = implementation.name == "micropython"

if IS_MICROPYTHON:
    log.log("Micropython detected")
    import micropython
    micropython.kbd_intr(-1)

log.log("~ for debug mode")

def com_read(length=1):
    data = stdin.read(length)
    if (isinstance(data, str)):
        data = [ord(d) for d in data] #type: ignore
    return data

def com_write(data):
    if isinstance(data, (list, tuple)):
        for d in data:
            com_write(d)
        return

    if isinstance(data, int):
        data = chr(data)

    print(data, end='')


class Terminated(Exception):
    pass

def pingHandler():
    data = com_read(2)
    if data[0] == 0x24:
        log.log("Ping request")
        com_write([0x62, 0x22, 0x40, 0x00])
    elif data[0] == 0x21:
        log.log("Version request")
        com_write([0x63, 0x21, 0x6B, 0x01, 0x28])

def debugHandler():
    while True:
        print("Debug Menu:")
        print("  0) Return to aLink mode")
        print("  1) View log")
        print("  x) Exit script")
        print("")

        while True:
            c = stdin.read(1)
            if c == '0':
                print("Returning to aLink mode")
                return

            elif c == '1':
                memlog.output(print)
                print("")
                break

            elif c == 'x':
                print("Exit requested")
                raise Terminated()

def unrecognisedHandler():
    log.warn("Unrecognised sequence")

ROOT_HANDLERS = {
    0x21: pingHandler,
    ord('~'): debugHandler
}

try:
    while True:
        c = com_read()
        handler = ROOT_HANDLERS.get(c[0]) or unrecognisedHandler
        handler()

except Terminated:
    pass

finally:
    if IS_MICROPYTHON:
        # Restore CTRL+C for Micropython environments
        log.log("Enabling Micropython keyboard interrupt")
        micropython.kbd_intr(3)

log.log("aLink shutdown")