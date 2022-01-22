from sys import stdin
import lcd
import log

ENABLE_LCD = True

if ENABLE_LCD:
    log.init(lcd.Screen())

log.log("Starting...")
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
        com_write([0x62, 0x22, 0x40, 0x00])
    elif data[0] == 0x21:
        com_write([0x63, 0x21, 0x6B, 0x01, 0x28])

def debugHandler():
    print("Debug Menu:")
    print("  0) Return to aLink mode")
    print("  x) Exit script")
    print("")

    while True:
        c = stdin.read(1)
        if c == '0':
            print("Returning to aLink mode")
            return
        elif c == 'x':
            raise Terminated()

def unrecognisedHandler():
    pass

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

log.log("aLink shutdown")