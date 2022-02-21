import os
from sys import stderr

CONFIG = """MEM_LOG_SIZE = 500
LCD_LOGGER = None
STDOUT_LOGGER = False
LOG_PING = False
DEVICE_VERSION = 107
DEBUG_LOCO = 9999
"""

FILES = [
    "alink.py",
    "main.py",
    "com.py",
    ("pico_config.py", "config.py"),
    "debug.py",
    "lcd_rp2040lcd096.py",
    "lcdlog.py",
    "log.py",
    "memlog.py",
]

def copy_to_pico(source, dest=None):
    dest = dest or source
    exit_code = os.system(f"mpremote fs cp ./{source} :{dest}")
    if exit_code != 0:
        raise OSError(f"Command exited with {exit_code}\n")

def is_mpremote_installed():
    try:
        import mpremote
        return True
    except ModuleNotFoundError:
        return False

def main():
    print("Installing pico-alink to attached device with default settings...")

    if not is_mpremote_installed():
        stderr.write("    *** mpremote is not installed ***")
        exit(1)

    with open("pico_config.py", "w") as cf:
        cf.write(CONFIG)

    for file in FILES:
        if isinstance(file, str):
            file = (file,)
        copy_to_pico(*file)

    print("Installation successful!")

if __name__ == "__main__":
    main()