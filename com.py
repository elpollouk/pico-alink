from sys import stdin

def checksum(data):
    checkSum = 0
    for v in data:
        checkSum ^= v
    return checkSum & 0xFF

def read(length=1):
    data = stdin.buffer.read(length)
    if (isinstance(data, str)):
        data = [ord(d) for d in data]
    return data

def read_byte():
    return read(1)[0]

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
    write(checksum(data))
