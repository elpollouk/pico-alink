import os
from sys import stderr

PICO_CONFIG_NAME = "pico_config.py"

PICO_CONFIG = """MEM_LOG_SIZE = 500
LCD_LOGGER = None
STDOUT_LOGGER = False
LOG_PING = False
LED_PIN = 25
LED_INITIAL_VALUE = 0
SCHEDULER_PERIOD = 1000
DEVICE_VERSION = 107
DEBUG_LOCO = 9999
"""

FILES = [
    "alink.py",
    "main.py",
    "com.py",
    (PICO_CONFIG_NAME, "config.py"),
    "debug.py",
    "eventcom_micropy.py",
    "lcd_rp2040lcd096.py",
    "lcdlog.py",
    "log.py",
    "memlog.py",
    "scheduler.py"
]

def copy_to_pico(source, dest=None):
    dest = dest or source
    exit_code = os.system(f"mpremote fs cp ./{source} :{dest}")
    if exit_code != 0:
        stderr.write(f"mpremote exited with exit code {exit_code}\n")
        exit(exit_code)

def is_mpremote_installed():
    try:
        import mpremote
        return True
    except ModuleNotFoundError:
        return False

def main():
    print("Installing pico-alink to attached device...")

    if not is_mpremote_installed():
        stderr.write("    *** mpremote is not installed ***")
        exit(1)

    if os.path.exists(PICO_CONFIG_NAME):
        print(f"Existing {PICO_CONFIG_NAME} found")
    else:
        print(f"Generating default {PICO_CONFIG_NAME}...")
        with open(PICO_CONFIG_NAME, "w") as config:
            config.write(PICO_CONFIG)

    print("Copying files to device...")
    for file in FILES:
        if isinstance(file, str):
            file = (file,)
        copy_to_pico(*file)

    print("Installation successful!")

if __name__ == "__main__":
    main()