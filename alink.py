# pyright: reportMissingImports=false
from sys import stdin, implementation
import com
import config
import log
import memlog
import os
import time


VERSION = "v0.2"
IS_MICROPYTHON = implementation.name == "micropython"
BOOT_TIME = time.time()
STATS = {}

# Loco function bit mapping by bank
FUNCTIONS = {
    0x20: (1, 2, 3, 4, 0),
    0x21: (5, 6, 7, 8),
    0x22: (9, 10, 11, 12),
    0x23: (13, 14, 15, 16, 17, 18, 19, 20),
    0x28: (21, 22, 23, 24, 25, 26, 27, 27)
}

# CV data store
current_cv = 0
cvs = [0] * 256
cvs[1] = 3
cvs[3] = 5
cvs[4] = 5
cvs[7] = 100
cvs[8] = 255
cvs[10] = 128
cvs[29] = 6


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

def inc_stat(stat):
    v = STATS.get(stat, 0) + 1
    STATS[stat] = v

def binary_mode(enabled):
    if IS_MICROPYTHON:
        import micropython
        micropython.kbd_intr(-1 if enabled else 3)


###################################################################################################
# Handlers
###################################################################################################

def unrecognisedHandler(buffer):
    sequence = com.to_hex(buffer)
    log.warn(sequence)


def pingHandler(_):
    if (config.LOG_PING):
        log.log("Ping request")
    com.write_with_checksum((0x62, 0x22, 0x40))


def versionHandler(_):
    log.log("Version request")
    com.write_with_checksum((0x63, 0x21, config.DEVICE_VERSION, 0x01))


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
    log.log(f" Loco: {loco}")
    log.log(f" Speed: {speed}")
    log.log(f" Forward: {forward}")


def locoFunctionHandler(buffer):
    bank = buffer[-1]
    loco = com.read_into_buffer(buffer, 2)
    state = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.validate_message(buffer, checksum):
        return

    loco = com.decode_loco_id(loco)

    log.log("Loco func request")
    log.log(f" Loco: {loco}")

    buffer = []
    bit = 1
    for f in FUNCTIONS[bank]:
        f = f"F{f}"
        f += "+" if state & bit != 0 else "-"
        buffer.append(f)
        bit <<= 1
        if len(buffer) == 4:
            log.log(" " + " ".join(buffer))
            buffer = []

    if buffer:
        log.log(" " + " ".join(buffer))


def cvSelectHandler(buffer):
    global current_cv
    cv = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.validate_message(buffer, checksum):
        return

    log.log(f"Selected CV {cv}")
    current_cv = cv

    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x01))
    com.write_with_checksum((0x61, 0x01))


def cvReadHandler(_):
    log.log(f"Reading CV {current_cv}")
    log.log(f" Value: {cvs[current_cv]}")
    com.write_with_checksum((0x63, 0x14, current_cv, cvs[current_cv]))


def cvWriteHandler(buffer):
    global current_cv
    cv = com.read_into_buffer(buffer, 1)[0]
    value = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.validate_message(buffer, checksum):
        return

    log.log(f"Writing CV {cv}")
    log.log(f" Value: {value}")

    current_cv = cv
    cvs[cv] = value

    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x01))
    com.write_with_checksum((0x61, 0x01))


def debugHandler(_):
    binary_mode(False)
    try:
        while True:
            print("")
            print("Debug Menu:")
            print("  0) Return to aLink mode")
            print("  1) View log")
            print("  2) Stats")
            print("  3) Memory info")
            print("  4) Trigger exception")
            print("  5) Delete boot.py")
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
                    ss = int(time.time() - BOOT_TIME)
                    mm = int(ss / 60)
                    ss -= (mm * 60)
                    print(f"Uptime: {mm:02d}:{ss:02d}")
                    for k, v in STATS.items():
                        print(f"{k}: {v}")
                    break

                elif c == '3':
                    if IS_MICROPYTHON:
                        import micropython
                        micropython.mem_info()
                    else:
                        print("Unavailable")
                    break

                elif c == '4':
                    print("Throwing exception...")
                    raise AssertionError("Test Exception")

                elif c == '5':
                    if not IS_MICROPYTHON:
                        print("Unavailable")
                        break
                    
                    try:
                        os.stat("boot.py")
                        print("Removing boot.py")
                        os.remove("boot.py")
                    except OSError:
                        print("boot.py not found")
                    break

                elif c == 'x':
                    print("Exit requested")
                    raise Terminated()

    finally:
        binary_mode(True)


ROOT_HANDLERS = [
    ((0x21, 0x10, 0x31), cvReadHandler),
    ((0x21, 0x21, 0x00), versionHandler),
    ((0x21, 0x24, 0x05), pingHandler),
    ((0x22, 0x15), cvSelectHandler),
    ((0x23, 0x16), cvWriteHandler),
    ((0xE4, 0x13), locoSpeedHandler),
    ((0xE4, 0x20), locoFunctionHandler),
    ((0xE4, 0x21), locoFunctionHandler),
    ((0xE4, 0x22), locoFunctionHandler),
    ((0xE4, 0x23), locoFunctionHandler),
    ((0xE4, 0x28), locoFunctionHandler),
    ((ord('~'),), debugHandler)
]


###################################################################################################
# Main script
###################################################################################################

log.log(f"alink {VERSION}")
log.log("Starting...")

binary_mode(True)

ROOT_HANDLERS = build_handler_trie()

log.log("~ for debug mode")

try:
    while True:
        try:
            node = ROOT_HANDLERS
            buffer = []
            while True:
                c = com.read_byte()
                buffer.append(c)
                node = node.get(c, unrecognisedHandler)
                if callable(node):
                    node(buffer)
                    if node == unrecognisedHandler:
                        inc_stat("Unhandled messages")
                    else:
                        inc_stat("Handled messages")
                    break

        except Terminated:
            break

        except Exception as ex:
            inc_stat("Exceptions")
            if IS_MICROPYTHON:
                from debug import ExceptionParser
                parser = ExceptionParser(ex)
                log.error(parser.details)
                log.error(f"  {parser.function}()")
                log.error(f"  {parser.location}")
            else:
                log.error(f"{type(ex).__name__}: {ex}")

finally:
    binary_mode(False)

log.log("aLink shutdown")