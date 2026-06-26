import asyncio
from typing import Optional, Callable, Awaitable, Any
from dataclasses import dataclass
from datetime import datetime
import random

from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: int = 2
    max_delay_seconds: int = 60
    jitter: bool = True


class RetryPolicy:
    """Configurable retry policy with exponential backoff."""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.config.base_delay_seconds * (2 ** attempt)
        delay = min(delay, self.config.max_delay_seconds)

        if self.config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def should_retry(self, attempt: int, error: Optional[Exception] = None) -> bool:
        """Check if retry should be attempted."""
        if attempt >= self.config.max_attempts:
            return False

        # Don't retry certain errors
        if error:
            if isinstance(error, ValueError):
                return False
            if "403" in str(error) or "Forbidden" in str(error):
                return False

        return True


class RetryExecutor:
    """Executes async operations with retry."""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()

    async def execute(
        self,
        operation: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with retries."""
        last_error: Optional[Exception] = None
        attempt = 0

        while True:
            try:
                if attempt > 0:
                    delay = self.retry_policy.get_delay(attempt - 1)
                    logger.info("retry_wait", attempt=attempt, delay=delay)
                    await asyncio.sleep(delay)

                result = await operation(*args, **kwargs)
                if attempt > 0:
                    logger.info("retry_success", attempt=attempt)
                return result

            except Exception as e:
                last_error = e
                attempt += 1

                logger.warning(
                    "retry_attempt_failed",
                    attempt=attempt,
                    max_attempts=self.retry_policy.config.max_attempts,
                    error=str(e)
                )

                if not self.retry_policy.should_retry(attempt, e):
                    raise last_error from e

        raise last_error if last_error else RuntimeError("Retry failed")
