import redis
import random
from typing import Optional, List, Dict, Any
from datetime import datetime

from survey_finder.config.settings import settings
from survey_finder.logging.logger import init_logger

logger = init_logger()


class ProxyManager:
    """Manages proxy rotation for adapters."""

    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._proxy_cache: List[str] = []
        self._last_refresh: Optional[datetime] = None

    def add_proxy(self, proxy_url: str) -> None:
        """Add a proxy to the pool."""
        key = "proxies"
        self.redis.sadd(key, proxy_url)
        self._proxy_cache = []
        logger.info("proxy_added", proxy=proxy_url)

    def remove_proxy(self, proxy_url: str) -> None:
        """Remove a proxy from the pool."""
        key = "proxies"
        self.redis.srem(key, proxy_url)
        self._proxy_cache = []
        logger.info("proxy_removed", proxy=proxy_url)

    def get_proxy(self) -> Optional[str]:
        """Get a random proxy from the pool."""
        proxies = self._get_proxies()
        if not proxies:
            return None
        return random.choice(proxies)

    def mark_failed(self, proxy_url: str) -> None:
        """Mark a proxy as failed and remove it."""
        self.remove_proxy(proxy_url)
        logger.warning("proxy_failed", proxy=proxy_url)

    def _get_proxies(self) -> List[str]:
        """Get all proxies from Redis."""
        key = "proxies"
        return list(self.redis.smembers(key))

    def refresh_cache(self) -> None:
        """Refresh local cache from Redis."""
        self._proxy_cache = self._get_proxies()
        self._last_refresh = datetime.utcnow()
