import io
import re
import sys

STACK_DETAILS = re.compile("File \"(.+)\".+line (\d+).+in (.+)")

class ExceptionParser(io.IOBase):
    def __init__(self, ex):
        self.ex = ex
        self.type = type(ex).__name__
        self.message = str(ex)
        self.file = ""
        self.line = ""
        self.function = ""
        self._buffer = ""
        sys.print_exception(ex, self)
        
    def _on_line(self):
        match = STACK_DETAILS.search(self._buffer)
        if match:
            self.file = match.group(1)
            self.line = match.group(2)
            self.function = match.group(3)
        
    def write(self, data):
        data = data.decode()
        for i in range(len(data)):
            c = data[i]
            if c == "\n":
                self._on_line()
                self._buffer = ""
            else:
                self._buffer += c

    @property
    def details(self):
        return f"{self.type}: {self.message}"
    
    @property
    def location(self):
        return f"{self.file}:{self.line}"

