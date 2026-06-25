import structlog

log = structlog.get_logger()

class ExecutionGuard:
    def __init__(self, leader_service):
        self.leader_service = leader_service

    def ensure_leader(self):
        if not self.leader_service.is_leader():
            log.warning("execution_skipped_not_leader")
            return False
        return True
