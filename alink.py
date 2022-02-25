# pyright: reportMissingImports=false
from debug import Terminated, IS_MICROPYTHON, inc_stat
import com
import config
import debug
import log
import scheduler


# Current version of this implementation
VERSION = "v0.4"

# Loco function bit mapping by bank
#   key: Bank number
#   values: Tuple of function ids in their bit order from lowest bit to highest bit
FUNCTIONS = {
    0x20: (1, 2, 3, 4, 0),
    0x21: (5, 6, 7, 8),
    0x22: (9, 10, 11, 12),
    0x23: (13, 14, 15, 16, 17, 18, 19, 20),
    0x28: (21, 22, 23, 24, 25, 26, 27, 28)
}

# Functions available on the "debug" loco (9999 by default)
DEBUG_FUNCTIONS = {
    0: debug.function_view_stats,
    1: debug.led_value,
    27: debug.function_delete_mainpy,
    28: debug.function_exit_script
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


###################################################################################################
# Trie
# We use a trie to match incoming bytes to their eventual handler
###################################################################################################

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

# Micropython needs to be told not to interpret byte value 3 on stdin as Ctrl+C
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
        log.info("Ping request")
    com.write_with_checksum((0x62, 0x22, 0x40))


def versionHandler(_):
    log.info("Version request")
    com.write_with_checksum((0x63, 0x21, config.DEVICE_VERSION, 0x01))


def locoSpeedHandler(buffer):
    loco = com.read_into_buffer(buffer, 2)
    speed = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.is_valid_message(buffer, checksum):
        return

    loco = com.decode_loco_id(loco)
    forward = speed & 0x80 == 0x80
    speed = speed & 0x7f

    log.info("Loco speed request")
    log.info(f" Loco: {loco}")
    log.info(f" Speed: {speed}")
    log.info(f" Forward: {forward}")


def debugFunctionHandler(bank, state):
    bit = 1

    for f in FUNCTIONS[bank]:
        active = state & bit != 0
        action = DEBUG_FUNCTIONS.get(f, lambda _: None)
        action(active)
        bit <<= 1


def locoFunctionHandler(buffer):
    bank = buffer[-1]
    loco = com.read_into_buffer(buffer, 2)
    state = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.is_valid_message(buffer, checksum):
        return

    loco = com.decode_loco_id(loco)

    if loco == config.DEBUG_LOCO:
        debugFunctionHandler(bank, state)
        return

    log.info("Loco func request")
    log.info(f" Loco: {loco}")

    buffer = []
    bit = 1

    for f in FUNCTIONS[bank]:
        f = f"F{f}"
        f += "+" if state & bit != 0 else "-"
        buffer.append(f)
        if len(buffer) == 4:
            log.info(" " + " ".join(buffer))
            buffer = []

        bit <<= 1

    if buffer:
        log.info(" " + " ".join(buffer))


def cvSelectHandler(buffer):
    global current_cv
    cv = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.is_valid_message(buffer, checksum):
        return

    log.info(f"Selected CV {cv}")
    current_cv = cv

    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x01))
    com.write_with_checksum((0x61, 0x01))


def cvReadHandler(_):
    log.info(f"Reading CV {current_cv}")
    log.info(f" Value: {cvs[current_cv]}")
    com.write_with_checksum((0x63, 0x14, current_cv, cvs[current_cv]))


def cvWriteHandler(buffer):
    global current_cv
    cv = com.read_into_buffer(buffer, 1)[0]
    value = com.read_into_buffer(buffer, 1)[0]
    checksum = com.read_byte()
    if not com.is_valid_message(buffer, checksum):
        return

    log.info(f"Writing CV {cv}")
    log.info(f" Value: {value}")

    current_cv = cv
    cvs[cv] = value

    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x02))
    com.write_with_checksum((0x61, 0x01))
    com.write_with_checksum((0x61, 0x01))


def debugHandler(_):
    binary_mode(False)
    try:
        debug.open_debug_menu()
    finally:
        binary_mode(True)


# Handlers are registered by associating a trigger byte sequence with a function to invoke.
# This list gets reparsed into a trie for more optimal lookup at run time.
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

ROOT_HANDLERS = build_handler_trie()

###################################################################################################
# Main script
###################################################################################################

def main():
    log.info(f"alink {VERSION}")
    log.info("Starting...")
    log.info("~ for debug mode")

    # We expect binary data over stdin, so disable Micropython's Ctrl+C interrupt
    binary_mode(True)

    try:
        while True:
            try:
                # Start of a new byte sequence
                node = ROOT_HANDLERS
                buffer = []

                # Keep reading bytes until we reach the end of a recognised sequence
                while True:
                    c = com.read_byte(scheduler.do_events, config.SCHEDULER_PERIOD)
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
                debug.log_exception(ex)

    finally:
        binary_mode(False)

    log.info("aLink shutdown")

if __name__ == "__main__":
    main()