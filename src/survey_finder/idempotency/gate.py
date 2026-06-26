import redis
import json
from typing import Optional, Tuple
from datetime import datetime, timedelta

from survey_finder.config.settings import settings
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class IdempotencyCheckResult:
    """Result of idempotency check."""

    def __init__(self, status: str, idempotency_key: str, first_seen_at: Optional[datetime] = None):
        self.status = status  # ACCEPTED, DUPLICATE, REJECTED
        self.idempotency_key = idempotency_key
        self.first_seen_at = first_seen_at


class RedisIdempotencyGate:
    """Redis-based idempotency gate with atomic operations."""

    def __init__(self, ttl_seconds: int = 86400):  # 24 hours default
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl = ttl_seconds

    def check_and_set(self, key: str) -> IdempotencyCheckResult:
        """
        Check if key exists and atomically set it.

        Returns:
            IdempotencyCheckResult with status
        """
        lock_key = f"idempotency:{key}"
        exists = self.redis.get(lock_key)

        if exists:
            logger.info("idempotency_duplicate", key=key)
            return IdempotencyCheckResult(
                status="DUPLICATE",
                idempotency_key=key,
                first_seen_at=datetime.fromisoformat(exists)
            )

        # Atomic set with TTL
        now = datetime.utcnow().isoformat()
        result = self.redis.set(lock_key, now, nx=True, ex=self.ttl)

        if result:
            logger.info("idempotency_accepted", key=key)
            return IdempotencyCheckResult(
                status="ACCEPTED",
                idempotency_key=key,
                first_seen_at=datetime.utcnow()
            )

        # Race condition - someone else set it
        existing = self.redis.get(lock_key)
        return IdempotencyCheckResult(
            status="DUPLICATE",
            idempotency_key=key,
            first_seen_at=datetime.fromisoformat(existing) if existing else None
        )

    def clear(self, key: str) -> None:
        """Clear idempotency key (for testing)."""
        lock_key = f"idempotency:{key}"
        self.redis.delete(lock_key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        lock_key = f"idempotency:{key}"
        return bool(self.redis.exists(lock_key))

    def get_timestamp(self, key: str) -> Optional[datetime]:
        """Get timestamp when key was first seen."""
        lock_key = f"idempotency:{key}"
        value = self.redis.get(lock_key)
        if value:
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass
        return None
