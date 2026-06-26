from enum import Enum
from dataclasses import dataclass
from typing import Optional

from survey_finder.buffer.queue import RedisBuffer
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class BackpressureSignal(str, Enum):
    OK = "ok"
    SLOW = "slow"
    FULL = "full"


@dataclass
class BackpressureState:
    signal: BackpressureSignal
    usage_ratio: float
    size: int
    max_size: int


class BackpressureController:
    """Controls backpressure based on buffer usage."""

    def __init__(
        self,
        buffer: RedisBuffer,
        slow_threshold: float = 0.7,
        full_threshold: float = 0.9
    ):
        self.buffer = buffer
        self.slow_threshold = slow_threshold
        self.full_threshold = full_threshold
        self._last_signal = BackpressureSignal.OK

    def check(self) -> BackpressureState:
        """Check current backpressure state."""
        usage_ratio = self.buffer.get_usage_ratio()
        size = self.buffer.size()
        max_size = self.buffer.max_size

        if usage_ratio >= self.full_threshold:
            signal = BackpressureSignal.FULL
        elif usage_ratio >= self.slow_threshold:
            signal = BackpressureSignal.SLOW
        else:
            signal = BackpressureSignal.OK

        if signal != self._last_signal:
            logger.info(
                "backpressure_changed",
                signal=signal.value,
                usage_ratio=usage_ratio,
                size=size,
                max_size=max_size
            )
            self._last_signal = signal

        return BackpressureState(
            signal=signal,
            usage_ratio=usage_ratio,
            size=size,
            max_size=max_size
        )

    def should_stop_cycle(self) -> bool:
        """Check if cycle should stop due to backpressure."""
        state = self.check()
        return state.signal == BackpressureSignal.FULL

    def should_slow_down(self) -> bool:
        """Check if cycle should slow down."""
        state = self.check()
        return state.signal in (BackpressureSignal.SLOW, BackpressureSignal.FULL)
