from sys import stdin, stdout
from debug import add_stat
import log

def to_hex(buffer):
    return " ".join([hex(v) for v in buffer])

def decode_loco_id(buffer):
    if (buffer[0] & 0xC0) == 0xC0:
        return ((buffer[0] & 0x3F) << 8) | buffer[1]

    return buffer[1]

def calc_checksum(data):
    checkSum = 0
    for v in data:
        checkSum ^= v
    return checkSum & 0xFF

def is_valid_message(buffer, checksum):
    if checksum == calc_checksum(buffer):
        return True

    log.error("Checksum failed")
    log.warn(f"Msg: {to_hex(buffer)}")

    return False

def read(length):
    data = stdin.buffer.read(length)
    if (isinstance(data, str)):
        data = [ord(d) for d in data]

    add_stat("Read", len(data))
    return data

def read_byte():
    return read(1)[0]

def read_into_buffer(buffer, length=1):
    data = read(length)
    buffer.extend(data)
    return data

def write(data):
    if isinstance(data, int):
        data = [data]
    data = bytes(data)
    stdout.buffer.write(data)
    add_stat("Written", len(data))

def write_with_checksum(data):
    write(data)
    write(calc_checksum(data))
