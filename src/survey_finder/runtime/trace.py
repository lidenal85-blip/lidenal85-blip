from dataclasses import dataclass, field
import time
import uuid

@dataclass
class TraceContext:
    cycle_id: str
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: float = field(default_factory=time.time)

    def child(self):
        return self
