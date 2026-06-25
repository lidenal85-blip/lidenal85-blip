import threading
import time

class ShutdownController:
    def __init__(self):
        self._lock = threading.Lock()
        self._shutdown = False
        self._draining = False

    def initiate_shutdown(self):
        with self._lock:
            self._shutdown = True
            self._draining = True

    def is_shutdown(self) -> bool:
        return self._shutdown

    def is_draining(self) -> bool:
        return self._draining

    def wait_for_drain(self, buffer, timeout: int = 10):
        start = time.time()
        while time.time() - start < timeout:
            if buffer.size() == 0:
                self._draining = False
                return True
            time.sleep(0.2)
        return False
