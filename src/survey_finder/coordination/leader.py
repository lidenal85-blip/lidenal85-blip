import time
from survey_finder.coordination.lease import LeaseManager
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class LeaderElectionService:
    """Distributed leader election using Redis lease."""

    def __init__(self, lease_manager: LeaseManager, service_id: str, ttl_seconds: int = 30):
        self.lease_manager = lease_manager
        self.service_id = service_id
        self.ttl = ttl_seconds
        self._is_leader = False

    def try_become_leader(self) -> bool:
        """Try to acquire leadership lease."""
        try:
            with self.lease_manager.acquire("leader_lock"):
                self._is_leader = True
                logger.info("became_leader", service_id=self.service_id)
                return True
        except RuntimeError:
            self._is_leader = False
            logger.debug("leader_lock_held", service_id=self.service_id)
            return False

    def is_leader(self) -> bool:
        """Check if this instance is the leader."""
        return self._is_leader

    def heartbeat(self):
        """Extend leadership lease."""
        if self._is_leader:
            self.lease_manager.heartbeat("leader_lock")
