from threading import Lock

class IdempotencyGate:
    """
    In-memory deduplication gate (production replacement: Redis/SQL unique constraint)
    """

    def __init__(self):
        self._seen = set()
        self._lock = Lock()

    def check_and_set(self, key: str) -> bool:
        with self._lock:
            if key in self._seen:
                return False
            self._seen.add(key)
            return True
