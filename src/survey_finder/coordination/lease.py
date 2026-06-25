import time
import uuid
import redis
from survey_finder.config.settings import settings

class LeaseError(Exception):
    pass

class RedisLeaseProvider:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.instance_id = str(uuid.uuid4())

    def try_acquire(self) -> bool:
        return self.redis.set(
            settings.LEADER_KEY,
            self.instance_id,
            nx=True,
            ex=settings.LEADER_TTL_SEC
        )

    def renew(self) -> bool:
        current = self.redis.get(settings.LEADER_KEY)
        if current != self.instance_id:
            return False
        return self.redis.expire(settings.LEADER_KEY, settings.LEADER_TTL_SEC)

    def is_leader(self) -> bool:
        return self.redis.get(settings.LEADER_KEY) == self.instance_id

    def release(self):
        current = self.redis.get(settings.LEADER_KEY)
        if current == self.instance_id:
            self.redis.delete(settings.LEADER_KEY)
