# pyright: reportMissingImports=false
from sys import stdin, implementation
import com
import config
import log
import memlog

IS_MICROPYTHON = implementation.name == "micropython"

class Terminated(Exception):
    pass

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


###################################################################################################
# Handlers
###################################################################################################

def unrecognisedHandler(buffer):
    sequence = com.to_hex(buffer)
    log.warn(sequence)

def pingHandler(_):
    log.log("Ping request")
    com.write_with_checksum([0x62, 0x22, 0x40])

def versionHandler(_):
    log.log("Version request")
    com.write_with_checksum([0x63, 0x21, config.DEVICE_VERSION, 0x01])

def locoSpeedHandler(buffer):
    loco = com.read_into_buffer(buffer, 2)
    speed = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.validate_message(buffer, checksum):
        return

    loco = com.decode_loco_id(loco)
    forward = speed & 0x80 == 0x80
    speed = speed & 0x7f

    log.log("Loco speed request")
    log.log(f"  Loco: {loco}")
    log.log(f"  Speed: {speed}")
    log.log(f"  Forward: {forward}")

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
                raise AssertionError("Test Exception")

            elif c == 'x':
                print("Exit requested")
                raise Terminated()


ROOT_HANDLERS = [
    ((0x21, 0x21, 0x00), versionHandler),
    ((0x21, 0x24, 0x05), pingHandler),
    ((0xE4, 0x13), locoSpeedHandler),
    ((ord('~'),), debugHandler)
]


###################################################################################################
# Main script
###################################################################################################

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
            c = com.read_byte()
            buffer.append(c)
            node = node.get(c, unrecognisedHandler)
            if callable(node):
                node(buffer)
                break

except Terminated:
    pass

except Exception as ex:
    if IS_MICROPYTHON:
        from debug import ExceptionParser
        parser = ExceptionParser(ex)
        log.error(parser.details)
        log.error(f"  {parser.function}()")
        log.error(f"  {parser.location}")
    else:
        log.error(f"{type(ex).__name__}: {ex}")
        

finally:
    if IS_MICROPYTHON:
        # Restore CTRL+C for Micropython environments
        micropython.kbd_intr(3)

log.log("aLink shutdown")