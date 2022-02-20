# pyright: reportMissingImports=false
import io
import re
import sys
import time

IS_MICROPYTHON = sys.implementation.name == "micropython"
STACK_DETAILS = re.compile("File \"(.+)\".+line (\d+).+in (.+)")
BOOT_TIME = time.time()
STATS = {}

class Terminated(Exception):
    pass

class ExceptionParser(io.IOBase):
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
    def details(self):
        return f"{self.type}: {self.message}"
    
    @property
    def location(self):
        return f"{self.file}:{self.line}"


###################################################################################################
# Stats
###################################################################################################

def inc_stat(stat):
    add_stat(stat, 1)

def add_stat(stat, value):
    value = STATS.get(stat, 0) + value
    STATS[stat] = value


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

def delete_bootpy(out):
    try:
        import os
        os.stat("boot.py")
        out("Removing boot.py")
        os.remove("boot.py")
    except OSError:
        out("boot.py not found")

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
    ("4", "Trigger exception", raise_exception, ALL),
    ("5", "Delete boot.py", delete_bootpy, MICROPYTHON),
    ("x", "Exit script", exit_script, ALL)
]

DEBUG_ACTION_MAP = {}
for item in DEBUG_MENU_ITEMS:
    if should_display(item):
        DEBUG_ACTION_MAP[item[0]] = item[2]
