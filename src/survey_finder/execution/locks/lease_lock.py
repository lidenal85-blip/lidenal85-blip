import time
from threading import Lock

class LeaseLock:
    """
    TTL-based lease lock to prevent stale orchestration deadlocks.
    """

    def __init__(self, ttl_sec: int = 120):
        self.ttl_sec = ttl_sec
        self._lock = Lock()
        self._owner = None
        self._expires_at = 0

    def acquire(self, owner: str) -> bool:
        with self._lock:
            now = time.time()

            if self._owner and now < self._expires_at:
                return False

            self._owner = owner
            self._expires_at = now + self.ttl_sec
            return True

    def release(self, owner: str):
        with self._lock:
            if self._owner == owner:
                self._owner = None
                self._expires_at = 0
