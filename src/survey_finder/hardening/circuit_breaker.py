import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime

from survey_finder.logging.logger import init_logger

logger = init_logger()


class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    timeout_seconds: int = 60
    half_open_max_attempts: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """Circuit breaker for external service calls."""

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()
        self._half_open_attempts = 0

    @property
    def state(self) -> CircuitState:
        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if self._last_failure_time:
                    elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                    if elapsed >= self.config.timeout_seconds:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_attempts = 0
                        logger.info("circuit_half_open", name=self.name)
                    else:
                        raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_attempts >= self.config.half_open_max_attempts:
                    self._state = CircuitState.OPEN
                    raise CircuitBreakerOpenError(f"Circuit {self.name} half-open max attempts exceeded")

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self._half_open_attempts = 0
                    logger.info("circuit_closed", name=self.name)
            else:
                self._failure_count = 0
                self._success_count = 0

    def _record_failure(self):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_attempts += 1
                logger.warning("circuit_half_open_failed",
                              name=self.name,
                              attempts=self._half_open_attempts)

            if self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._last_failure_time = datetime.utcnow()
                    logger.error("circuit_opened",
                                name=self.name,
                                failures=self._failure_count)

    def reset(self):
        """Reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_attempts = 0
            self._last_failure_time = None
            logger.info("circuit_reset", name=self.name)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
