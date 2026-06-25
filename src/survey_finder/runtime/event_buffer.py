from collections import deque
from typing import Any
import threading

class EventBuffer:
    def __init__(self, max_size: int = 1000):
        self._buffer = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._max_size = max_size
        self._closed = False

    def push(self, event: Any) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("Buffer closed (shutdown in progress)")

            if len(self._buffer) >= self._max_size:
                # hard backpressure signal
                raise RuntimeError("BACKPRESSURE_LIMIT_REACHED")

            self._buffer.append(event)

    def pop(self):
        with self._lock:
            if len(self._buffer) == 0:
                return None
            return self._buffer.popleft()

    def size(self):
        return len(self._buffer)

    def close(self):
        with self._lock:
            self._closed = True
