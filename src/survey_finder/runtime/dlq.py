from typing import List, Dict, Any
import threading

class DeadLetterQueue:
    def __init__(self):
        self._store: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def push(self, item: Dict[str, Any]) -> None:
        with self._lock:
            self._store.append(item)

    def size(self) -> int:
        return len(self._store)

    def dump(self) -> List[Dict[str, Any]]:
        return list(self._store)
