from dataclasses import dataclass, field
import time
from typing import Dict


@dataclass
class IdempotencyGate:
    ttl_seconds: int = 300
    _store: Dict[str, float] = field(default_factory=dict)

    def _cleanup(self):
        now = time.time()
        expired = [k for k, v in self._store.items() if now - v > self.ttl_seconds]
        for k in expired:
            del self._store[k]

    def check_and_set(self, key: str) -> bool:
        self._cleanup()

        if key in self._store:
            return False

        self._store[key] = time.time()
        return True
