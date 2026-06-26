import redis
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from survey_finder.config.settings import settings
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class RedisBuffer:
    """Redis-backed event buffer with backpressure support."""

    def __init__(self, buffer_key: str = "survey_buffer", max_size: int = 10000):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.buffer_key = buffer_key
        self.max_size = max_size

    def push(self, event: Dict[str, Any]) -> bool:
        """
        Push event to buffer.

        Returns:
            True if pushed, False if buffer full
        """
        current_size = self.redis.llen(self.buffer_key)
        if current_size >= self.max_size:
            logger.warning("buffer_full", current_size=current_size, max_size=self.max_size)
            return False

        event["queued_at"] = datetime.utcnow().isoformat()
        result = self.redis.lpush(self.buffer_key, json.dumps(event))
        logger.debug("buffer_push", key=self.buffer_key, size=current_size + 1)
        return True

    def pop(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Pop event from buffer.

        Args:
            timeout: Block timeout in seconds (0 for non-blocking)

        Returns:
            Event dict or None if empty
        """
        if timeout > 0:
            result = self.redis.brpop(self.buffer_key, timeout=timeout)
        else:
            result = self.redis.rpop(self.buffer_key)

        if not result:
            return None

        # If brpop, result is (key, value)
        if isinstance(result, tuple):
            value = result[1]
        else:
            value = result

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.error("buffer_decode_error", value=value[:100])
            return None

    def pop_batch(self, batch_size: int = 10, timeout: int = 1) -> List[Dict[str, Any]]:
        """Pop multiple events from buffer."""
        batch = []
        for _ in range(batch_size):
            event = self.pop(timeout=0)
            if event:
                batch.append(event)
            else:
                break
        return batch

    def size(self) -> int:
        """Get current buffer size."""
        return self.redis.llen(self.buffer_key)

    def clear(self) -> None:
        """Clear buffer."""
        self.redis.delete(self.buffer_key)

    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self.size() >= self.max_size

    def get_usage_ratio(self) -> float:
        """Get buffer usage ratio (0.0 - 1.0)."""
        return self.size() / self.max_size if self.max_size > 0 else 0.0
