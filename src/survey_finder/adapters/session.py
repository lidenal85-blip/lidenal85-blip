import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from survey_finder.config.settings import settings
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages adapter sessions with Redis persistence."""

    def __init__(self, ttl_seconds: int = 3600):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl = ttl_seconds
        self._session_cache: Dict[str, Dict[str, Any]] = {}

    def get_session(self, source: str) -> Optional[Dict[str, Any]]:
        """Get session data for source."""
        key = f"session:{source}"

        # Try cache first
        if source in self._session_cache:
            return self._session_cache[source]

        # Try Redis
        data = self.redis.get(key)
        if data:
            session = json.loads(data)
            self._session_cache[source] = session
            return session

        return None

    def save_session(self, source: str, session_data: Dict[str, Any]) -> None:
        """Save session data."""
        key = f"session:{source}"
        self._session_cache[source] = session_data
        self.redis.setex(key, self.ttl, json.dumps(session_data))
        logger.info("session_saved", source=source)

    def clear_session(self, source: str) -> None:
        """Clear session for source."""
        key = f"session:{source}"
        if source in self._session_cache:
            del self._session_cache[source]
        self.redis.delete(key)
        logger.info("session_cleared", source=source)

    def is_valid(self, source: str) -> bool:
        """Check if session is still valid."""
        session = self.get_session(source)
        if not session:
            return False

        expires_at = session.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expires:
                    return False
            except (ValueError, TypeError):
                pass

        return True
