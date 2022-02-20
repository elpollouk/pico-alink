from msilib.schema import Error
import os

def copy_to_pico(source, dest=None):
    dest = dest or source
    exit_code = os.system(f"mpremote fs cp ./{source} :{dest}")
    if exit_code != 0:
        raise Error(f"Command exited with {exit_code}\n")


print("Installing pico-alink to attached device with default settings")

try:
    import mpremote
except ModuleNotFoundError:
    raise Error("mpremote is not installed")

with open("pico_config.py", "w") as cf:
    cf.write("""MEM_LOG_SIZE = 500
LCD_LOGGER = None
STDOUT_LOGGER = False
LOG_PING = False
DEVICE_VERSION = 107
DEBUG_LOCO = 9999
""")

copy_to_pico("alink.py")
copy_to_pico("boot.py")
copy_to_pico("com.py")
copy_to_pico("pico_config.py", "config.py")
copy_to_pico("debug.py")
copy_to_pico("lcd_rp2040lcd096.py")
copy_to_pico("lcdlog.py")
copy_to_pico("log.py")
copy_to_pico("memlog.py")

print("Installation successful!")