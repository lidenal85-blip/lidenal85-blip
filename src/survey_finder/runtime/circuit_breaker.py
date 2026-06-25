import time
import threading

class CircuitOpen(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

        self._failures = 0
        self._opened_at = 0
        self._state = "CLOSED"
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            if self._state == "OPEN":
                if time.time() - self._opened_at > self.reset_timeout:
                    self._state = "HALF_OPEN"
                    return True
                return False
            return True

    def success(self):
        with self._lock:
            self._failures = 0
            self._state = "CLOSED"

    def failure(self):
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = "OPEN"
                self._opened_at = time.time()
