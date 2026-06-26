import time
import threading
from uuid import uuid4
from dataclasses import dataclass
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)

@dataclass(frozen=True)
class CycleResult:
    cycle_id: str
    status: str
    duration_ms: int


class ExecutionController:
    """
    Single active cycle execution controller.
    Guarantees one active ingestion cycle at a time (in-process lock).
    """

    def __init__(self, cycle_timeout_sec: int = 60):
        self.cycle_timeout_sec = cycle_timeout_sec
        self._lock = threading.Lock()
        self._active_cycle_id = None

    def _acquire(self) -> str:
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("cycle_already_running")

        cycle_id = str(uuid4())
        self._active_cycle_id = cycle_id
        return cycle_id

    def _release(self):
        self._active_cycle_id = None
        self._lock.release()

    def run_cycle(self, handler):
        cycle_id = self._acquire()
        start = time.time()

        logger.info("cycle_start", cycle_id=cycle_id)

        try:
            handler(cycle_id)
            status = "success"
        except Exception as e:
            logger.error("cycle_failed", cycle_id=cycle_id, error=str(e))
            status = "failed"
        finally:
            self._release()

        duration_ms = int((time.time() - start) * 1000)

        logger.info(
            "cycle_end",
            cycle_id=cycle_id,
            status=status,
            duration_ms=duration_ms,
        )

        return CycleResult(cycle_id, status, duration_ms)
