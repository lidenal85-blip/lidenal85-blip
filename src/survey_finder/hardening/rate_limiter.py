import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional

from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimiterConfig:
    requests_per_minute: int = 60
    burst_size: int = 10


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self,
        name: str,
        config: Optional[RateLimiterConfig] = None
    ):
        self.name = name
        self.config = config or RateLimiterConfig()
        self._tokens = self.config.burst_size
        self._last_refill = time.time()
        self._lock = threading.Lock()
        self._rate = self.config.requests_per_minute / 60.0  # tokens per second

    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Acquire tokens with optional timeout."""
        start_time = time.time()

        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

            if timeout is not None and (time.time() - start_time) >= timeout:
                logger.warning("rate_limit_timeout", name=self.name, tokens=tokens)
                return False

            time.sleep(0.1)

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        new_tokens = elapsed * self._rate
        self._tokens = min(self.config.burst_size, self._tokens + new_tokens)
        self._last_refill = now

    def get_available_tokens(self) -> float:
        """Get current available tokens."""
        with self._lock:
            self._refill()
            return self._tokens


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass
