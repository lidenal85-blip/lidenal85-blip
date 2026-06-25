import time
import threading

class LeaseLock:
    def __init__(self, ttl_seconds: int = 60):
        self._lock = threading.Lock()
        self._active = False
        self._expires_at = 0
        self._ttl = ttl_seconds

    def acquire(self, cycle_id: str) -> bool:
        with self._lock:
            now = time.time()

            # expired lease cleanup
            if self._active and now > self._expires_at:
                self._active = False

            if self._active:
                return False

            self._active = True
            self._expires_at = now + self._ttl
            return True

    def heartbeat(self) -> None:
        with self._lock:
            if self._active:
                self._expires_at = time.time() + self._ttl

    def release(self) -> None:
        with self._lock:
            self._active = False
            self._expires_at = 0
