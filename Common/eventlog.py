import time


class LogEvents:
    def __init__(self, callback):
        self.callback = callback
        self.current_time = time.strftime("%H:%M:%S")

    def log_error(self, msg):
        if self.callback:
            self.callback(f"[{self.current_time}][ERROR] {msg}")

    def log_info(self,msg):
        if self.callback:
            self.callback(f"[{self.current_time}][INFO] {msg}")

