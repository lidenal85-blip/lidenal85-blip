import threading

class DeliveryIdempotencyStore:
    """
    Prevent duplicate notifications per survey.
    """

    def __init__(self):
        self._seen = set()
        self._lock = threading.Lock()

    def mark_sent(self, key: str) -> bool:
        with self._lock:
            if key in self._seen:
                return False
            self._seen.add(key)
            return True
