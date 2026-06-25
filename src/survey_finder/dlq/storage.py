import redis
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from survey_finder.config.settings import settings
from survey_finder.contracts.dlq import DLQItem
from survey_finder.logging.logger import init_logger

logger = init_logger()


class DLQStorage:
    """Dead Letter Queue storage using Redis."""

    def __init__(self, ttl_seconds: int = 604800):  # 7 days default
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl = ttl_seconds

    def store(self, dlq_item: DLQItem) -> None:
        """Store DLQ item."""
        key = f"dlq:{dlq_item.cycle_id}:{dlq_item.source}"
        data = dlq_item.model_dump()
        data["stored_at"] = datetime.utcnow().isoformat()

        self.redis.lpush(key, json.dumps(data))
        self.redis.expire(key, self.ttl)

        logger.info("dlq_stored", cycle_id=dlq_item.cycle_id, source=dlq_item.source)

    def fetch_by_cycle(self, cycle_id: str, limit: int = 100) -> List[DLQItem]:
        """Fetch DLQ items for a cycle."""
        pattern = f"dlq:{cycle_id}:*"
        items: List[DLQItem] = []

        for key in self.redis.keys(pattern):
            raw_items = self.redis.lrange(key, 0, limit - 1)
            for item_json in raw_items:
                try:
                    data = json.loads(item_json)
                    items.append(DLQItem(**data))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error("dlq_decode_error", key=key, error=str(e))

            if len(items) >= limit:
                break

        return items

    def fetch_by_source(self, source: str, limit: int = 100) -> List[DLQItem]:
        """Fetch DLQ items for a source."""
        pattern = f"dlq:*:{source}"
        items: List[DLQItem] = []

        for key in self.redis.keys(pattern):
            raw_items = self.redis.lrange(key, 0, limit - 1)
            for item_json in raw_items:
                try:
                    data = json.loads(item_json)
                    items.append(DLQItem(**data))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error("dlq_decode_error", key=key, error=str(e))

            if len(items) >= limit:
                break

        return items

    def delete_by_cycle(self, cycle_id: str) -> int:
        """Delete all DLQ items for a cycle."""
        pattern = f"dlq:{cycle_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            return self.redis.delete(*keys)
        return 0

    def count(self, cycle_id: Optional[str] = None) -> int:
        """Count DLQ items."""
        if cycle_id:
            pattern = f"dlq:{cycle_id}:*"
        else:
            pattern = "dlq:*"

        return len(self.redis.keys(pattern))
