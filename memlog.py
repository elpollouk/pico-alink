from config import MEM_LOG_SIZE

INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"

_buffer = []
_size = 0

def info(text):
    _append(INFO, text)

def warn(text):
    _append(WARN, text)

def error(text):
    _append(ERROR, text)

def _append(level, text):
    global _size
    while len(text) + _size > MEM_LOG_SIZE:
        old = _buffer.pop(0)
        _size -= len(old[1])

    _buffer.append((level, text))
    _size += len(text)

def output(out):
    for level, text in _buffer:
        out(f"{level}: {text}")