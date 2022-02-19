import config
import memlog

_loggers = [
    memlog
]

if config.LCD_LOGGER:
    import lcdlog
    lcdlog.init(config.LCD_LOGGER.Screen())
    _loggers.append(lcdlog)


def log(text):
    _apply("log", text)
    
def warn(text):
    _apply("warn", text)
    
def error(text):
    _apply("error", text)

def _apply(method, text):
    for logger in _loggers:
        getattr(logger, method)(text)