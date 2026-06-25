from collections import deque
from threading import Lock

class BackpressureBuffer:
    """
    Bounded in-memory buffer with backpressure signal.
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._buffer = deque()
        self._lock = Lock()

    def push(self, event: dict) -> bool:
        with self._lock:
            if len(self._buffer) >= self.max_size:
                return False
            self._buffer.append(event)
            return True

    def pop_batch(self, batch_size: int = 10):
        with self._lock:
            out = []
            while self._buffer and len(out) < batch_size:
                out.append(self._buffer.popleft())
            return out

    def size(self) -> int:
        return len(self._buffer)
