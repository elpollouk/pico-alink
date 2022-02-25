# pyright: reportMissingImports=false
import config
import io
import log
import re
import scheduler
import sys
import time

IS_MICROPYTHON = sys.implementation.name == "micropython"
STACK_DETAILS = re.compile("File \"(.+)\".+line (\d+).+in (.+)")
BOOT_TIME = time.time()
STATS = {}

class Terminated(Exception):
    pass


###################################################################################################
# Parser for exceptions formatted by Micropython's sys.print_exception()
###################################################################################################

class ParseException(io.IOBase):
    def __init__(self, ex):
        self.ex = ex
        self.type = type(ex).__name__
        self.message = str(ex)
        self.file = ""
        self.line = ""
        self.function = ""
        self._buffer = ""
        sys.print_exception(ex, self)

    def _on_line(self):
        match = STACK_DETAILS.search(self._buffer)
        if match:
            self.file = match.group(1)
            self.line = match.group(2)
            self.function = match.group(3)

    def write(self, data):
        data = data.decode()
        for i in range(len(data)):
            c = data[i]
            if c == "\n":
                self._on_line()
                self._buffer = ""
            else:
                self._buffer += c

    @property
    def location(self):
        return f"{self.file}:{self.line}"

def log_exception(ex):
    inc_stat("Exceptions")
    if IS_MICROPYTHON:
        details = ParseException(ex)
        log.error(f"{details.type}: {details.message}")
        log.error(f"  {details.function}()")
        log.error(f"  {details.location}")
    else:
        log.error(f"{type(ex).__name__}: {ex}")


###################################################################################################
# Stats
###################################################################################################

def inc_stat(stat):
    add_stat(stat, 1)

def add_stat(stat, value):
    value = STATS.get(stat, 0) + value
    STATS[stat] = value


###################################################################################################
# Misc Helpers
###################################################################################################

LED = None
if IS_MICROPYTHON:
    from machine import Pin
    LED = Pin(config.LED_PIN, Pin.OUT)
    LED.value(config.LED_INITIAL_VALUE)
    log.info(f"Set pin {config.LED_PIN} to {config.LED_INITIAL_VALUE}")


def led_toggle():
    if LED:
        LED.toggle()

def led_value(value):
    if LED:
        LED.value(1 if value else 0)


###################################################################################################
# Debug Loco Functions
###################################################################################################

def function_view_stats(active):
    if (active):
        view_stats(log.info)

def function_delete_mainpy(active):
    if (active):
        delete_mainpy(log.info)

def function_exit_script(active):
    if (active):
        exit_script(log.info)


###################################################################################################
# Debug Menu
###################################################################################################

def return_to_alink(out):
    out("Returning to aLink mode")
    return True

def view_log(out):
    import memlog
    memlog.output(out)

def view_stats(out):
    ss = int(time.time() - BOOT_TIME)
    mm = int(ss / 60)
    ss -= (mm * 60)
    out(f"Uptime: {mm:02d}:{ss:02d}")
    for k, v in STATS.items():
        out(f"{k}: {v}")

def mem_info(_):
    import micropython
    micropython.mem_info()

def raise_exception(out):
    out("Throwing exception...")
    raise AssertionError("Test Exception")

def schedule_message(out):
    out("Scheduling test messae in 5 seconds")
    scheduler.run_in(5, log.info, ("Test",))

def schedule_exception(out):
    out("Scheduling test exception in 5 seconds")
    scheduler.run_in(5, raise_exception, (lambda _: None,))

def delete_mainpy(out):
    try:
        import os
        os.stat("main.py")
        out("Removing main.py")
        os.remove("main.py")
    except OSError:
        out("main.py not found")

def exit_script(out):
    out("Exit requested")
    raise Terminated()

def should_display(item):
    return item[3] == ALL or IS_MICROPYTHON

def open_debug_menu():
    while True:
        print("")
        print("Debug Menu:")
        for item in DEBUG_MENU_ITEMS:
            if should_display(item):
                print(f"  {item[0]}) {item[1]}")
        print("")

        while True:
            c = sys.stdin.read(1)
            action = DEBUG_ACTION_MAP.get(c)
            if action is None:
                continue

            if action(print):
                return

            break

ALL = object()
MICROPYTHON = object()

DEBUG_MENU_ITEMS = [
    ("0", "Return to aLink mode", return_to_alink, ALL),
    ("1", "View log", view_log, ALL),
    ("2", "Stats", view_stats, ALL),
    ("3", "Memory info", mem_info, MICROPYTHON),
    ("4", "Toggle onboard led", lambda _: led_toggle(), MICROPYTHON),
    ("5", "Trigger exception", raise_exception, ALL),
    ("6", "Schedule test message", schedule_message, ALL),
    ("7", "Schedule test exception", schedule_exception, ALL),
    ("8", "Delete main.py", delete_mainpy, MICROPYTHON),
    ("x", "Exit script", exit_script, ALL)
]

DEBUG_ACTION_MAP = {}
for item in DEBUG_MENU_ITEMS:
    if should_display(item):
        DEBUG_ACTION_MAP[item[0]] = item[2]
