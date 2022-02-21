_screen = None
_buffer = []

def init(device):
    global _screen, DEVICE, INFO, ERROR, WARN, BLACK
    DEVICE = device
    INFO = DEVICE.rgb(192, 192, 192)
    ERROR = DEVICE.rgb(192, 0, 0)
    WARN = DEVICE.rgb(192, 128, 0)
    BLACK = DEVICE.rgb(0, 0, 0)

    _screen = device.Screen()
    _screen.fill(BLACK)
    _screen.display()

def info(text):
    _append(text, INFO)

def warn(text):
    _append(text, WARN)

def error(text):
    _append(text, ERROR)

def _append(text, colour):
    global _buffer
    if _screen is None:
        return

    if not isinstance(text, str):
        text = str(text)

    while True:
        overflow = text[DEVICE.WIDTH:]
        text = text[:DEVICE.WIDTH]

        if (len(_buffer) == DEVICE.HEIGHT):
            _buffer = _buffer[1:]
            
        _buffer.append((colour, text))

        if not overflow:
            break
        text = overflow

    _render()
    
def _render():
    y = DEVICE.LINE_OFFSET_Y

    _screen.fill(BLACK)
    for line in _buffer:
        _screen.text(line[1], 0, y, line[0])
        y += DEVICE.LINE_HEIGHT
        
    _screen.display()
