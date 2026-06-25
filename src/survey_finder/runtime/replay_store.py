from typing import Dict, Any, List
import threading

class ReplayStore:
    def __init__(self):
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def record(self, cycle_id: str, event: Dict[str, Any]) -> None:
        with self._lock:
            if cycle_id not in self._store:
                self._store[cycle_id] = []
            self._store[cycle_id].append(event)

    def get(self, cycle_id: str) -> List[Dict[str, Any]]:
        return self._store.get(cycle_id, [])
