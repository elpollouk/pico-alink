import config
import memlog

_loggers = [
    memlog
]

if config.LCD_LOGGER:
    import lcdlog
    lcdlog.init(config.LCD_LOGGER)
    _loggers.append(lcdlog)

if config.STDOUT_LOGGER:
    class StdoutLogger:
        def log(self, text):
            print(f"INFO: {text}")
        def warn(self, text):
            print(f"WARN: {text}")
        def error(self, text):
            print(f"ERROR: {text}")

    _loggers.append(StdoutLogger())


def log(text):
    _apply("log", text)
    
def warn(text):
    _apply("warn", text)
    
def error(text):
    _apply("error", text)

def _apply(method, text):
    for logger in _loggers:
        getattr(logger, method)(text)