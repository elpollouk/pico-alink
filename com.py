from sys import stdin
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

def validate_message(buffer, checksum):
    if checksum == calc_checksum(buffer):
        return True

    log.error("Checksum failed")
    log.warn(f"Msg: {to_hex(buffer)}")

    return False

def read(length=1):
    data = stdin.buffer.read(length)
    if (isinstance(data, str)):
        data = [ord(d) for d in data]
    return data

def read_byte():
    return read(1)[0]

def read_into_buffer(buffer, length=1):
    data = read(length)
    buffer.extend(data)
    return data

def write(data):
    if isinstance(data, (list, tuple)):
        for d in data:
            write(d)
        return

    if isinstance(data, int):
        data = chr(data)

    print(data, end='')

def write_with_checksum(data):
    write(data)
    write(calc_checksum(data))
