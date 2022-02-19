# pyright: reportMissingImports=false
from sys import stdin, implementation
import config
import log
import memlog

IS_MICROPYTHON = implementation.name == "micropython"

def checksum(data):
    checkSum = 0
    for v in data:
        checkSum ^= v
    return checkSum & 0xFF

def com_read(length=1):
    data = stdin.buffer.read(length)
    if (isinstance(data, str)):
        data = [ord(d) for d in data]
    return data

def com_write(data):
    if isinstance(data, (list, tuple)):
        for d in data:
            com_write(d)
        return

    if isinstance(data, int):
        data = chr(data)

    print(data, end='')

def com_write_with_checksum(data):
    com_write(data)
    com_write(checksum(data))

class Terminated(Exception):
    pass

def pingHandler(buffer):
    log.log("Ping request")
    com_write_with_checksum([0x62, 0x22, 0x40])

def versionHandler(buffer):
    log.log("Version request")
    com_write_with_checksum([0x63, 0x21, config.DEVICE_VERSION, 0x01])

def debugHandler(buffer):
    while True:
        print("")
        print("Debug Menu:")
        print("  0) Return to aLink mode")
        print("  1) View log")
        print("  2) Memory info")
        print("  3) Trigger exception")
        print("  x) Exit script")
        print("")

        while True:
            c = stdin.read(1)
            if c == '0':
                print("Returning to aLink mode")
                return

            elif c == '1':
                memlog.output(print)
                break

            elif c == '2':
                if IS_MICROPYTHON:
                    micropython.mem_info()
                else:
                    print("Unavailable")
                break

            elif c == '3':
                print("Throwing exception...")
                raise NameError("Test Exception")

            elif c == 'x':
                print("Exit requested")
                raise Terminated()

def unrecognisedHandler(buffer):
    log.warn("Unrecognised request")
    sequence = " ".join([hex(v) for v in buffer])
    log.warn(sequence)


def add_to_trie(node, handler):
    sequence = handler[0]
    handler = handler[1]
    for b in sequence[:-1]:
        n = node.get(b)
        if not n:
            n = {}
            node[b] = n
        node = n

    node[sequence[-1]] = handler

def build_handler_trie():
    root = {}
    for handler in ROOT_HANDLERS:
        add_to_trie(root, handler)

    return root

ROOT_HANDLERS = [
    ((0x21, 0x21, 0x00), versionHandler),
    ((0x21, 0x24, 0x05), pingHandler),
    ((ord('~'),), debugHandler)
]



log.log("alink v0.1")
log.log("Starting...")

if IS_MICROPYTHON:
    log.log("Micropython detected")
    import micropython
    micropython.kbd_intr(-1)

ROOT_HANDLERS = build_handler_trie()

log.log("~ for debug mode")

try:
    while True:
        node = ROOT_HANDLERS
        buffer = []
        while True:
            c = com_read()[0]
            buffer.append(c)
            node = node.get(c, unrecognisedHandler)
            if callable(node):
                node(buffer)
                break

except Terminated:
    pass

except Exception as ex:
    log.error(f"{type(ex).__name__}: {ex}")

finally:
    if IS_MICROPYTHON:
        # Restore CTRL+C for Micropython environments
        log.log("Enabling Micropython keyboard interrupt")
        micropython.kbd_intr(3)

log.log("aLink shutdown")