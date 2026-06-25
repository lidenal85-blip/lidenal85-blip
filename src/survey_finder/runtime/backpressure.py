class BackpressureSignal(Exception):
    pass

class BackpressureManager:
    def __init__(self, buffer):
        self.buffer = buffer
        self._paused = False

    def can_accept(self) -> bool:
        return not self._paused

    def trigger(self):
        self._paused = True

    def release(self):
        self._paused = False
