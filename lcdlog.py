import lcd_rp2040lcd096

NORMAL = lcd_rp2040lcd096.rgb(192, 192, 192)
ERROR = lcd_rp2040lcd096.rgb(192, 0, 0)
WARN = lcd_rp2040lcd096.rgb(192, 128, 0)

WIDTH = 20
HEIGHT = 8
LINE_HEIGHT = 10
LINE_OFFSET_Y = 1

_screen = None
_buffer = []

def init(screen):
    global _screen
    _screen = screen
    _screen.fill(lcd_rp2040lcd096.BLACK)
    _screen.display()
    
def log(text):
    _append(text, NORMAL)
    
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

    text = text[:20]

    if (len(_buffer) == HEIGHT):
        _buffer = _buffer[1:]
        
    _buffer.append((colour, text))
    _render()
    
def _render():
    y = LINE_OFFSET_Y

    _screen.fill(lcd_rp2040lcd096.BLACK)
    for line in _buffer:
        _screen.text(line[1], 0, y, line[0])
        y += LINE_HEIGHT
        
    _screen.display()