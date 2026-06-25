import time
import threading
import structlog
from survey_finder.coordination.lease import RedisLeaseProvider
from survey_finder.config.settings import settings

log = structlog.get_logger()

class LeaderElectionService:
    def __init__(self):
        self.lease = RedisLeaseProvider()
        self.running = False
        self.is_leader_flag = False

    def start(self):
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running:
            try:
                if not self.is_leader_flag:
                    self.is_leader_flag = self.lease.try_acquire()
                    if self.is_leader_flag:
                        log.info("leader_acquired", instance=self.lease.instance_id)

                else:
                    ok = self.lease.renew()
                    if not ok:
                        self.is_leader_flag = False
                        log.warning("leader_lost")

                time.sleep(settings.HEARTBEAT_SEC)

            except Exception as e:
                log.error("leader_election_error", error=str(e))
                self.is_leader_flag = False
                time.sleep(2)

    def is_leader(self) -> bool:
        return self.is_leader_flag

    def get_leader_id(self):
        return self.lease.instance_id
