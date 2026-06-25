import time
import redis
from contextlib import contextmanager
from survey_finder.config.settings import settings


class LeaseManager:
    """Redis-based distributed lease manager."""

    def __init__(self, ttl_seconds: int = 60):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl = ttl_seconds

    @contextmanager
    def acquire(self, key: str):
        lock_key = f"lease:{key}"
        lock_value = str(time.time())

        acquired = self.redis.set(lock_key, lock_value, nx=True, ex=self.ttl)

        if not acquired:
            raise RuntimeError(f"Lease {key} already held")

        try:
            yield
        finally:
            current = self.redis.get(lock_key)
            if current and current == lock_value:
                self.redis.delete(lock_key)

    def heartbeat(self, key: str):
        lock_key = f"lease:{key}"
        self.redis.expire(lock_key, self.ttl)
