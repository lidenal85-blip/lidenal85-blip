import time
import uuid
import structlog

from survey_finder.coordination.leader import LeaderElectionService
from survey_finder.contracts.cycle import CycleContext
from survey_finder.config.settings import settings

log = structlog.get_logger()

class ExecutionController:
    """
    SINGLE ACTIVE EXECUTION GUARANTEE LAYER
    """

    def __init__(self, leader_service: LeaderElectionService):
        self.leader_service = leader_service
        self.instance_id = str(uuid.uuid4())
        self.running = True

    def build_cycle_context(self) -> CycleContext:
        return CycleContext(
            leader_id=str(self.leader_service.lease.instance_id),
            instance_id=self.instance_id
        )

    def run_cycle(self, cycle: CycleContext):
        """
        PLACEHOLDER: deterministic execution boundary
        """
        log.info(
            "cycle_started",
            cycle_id=cycle.cycle_id,
            leader_id=cycle.leader_id,
            instance_id=cycle.instance_id
        )

        # deterministic simulation of pipeline stages
        time.sleep(0.2)

        log.info(
            "cycle_finished",
            cycle_id=cycle.cycle_id
        )

    def run(self):
        """
        MAIN ORCHESTRATION LOOP
        """
        log.info("execution_controller_started", instance_id=self.instance_id)

        while self.running:
            try:
                # HARD GATE: only leader executes
                if not self.leader_service.is_leader():
                    log.info("standby_mode", instance_id=self.instance_id)
                    time.sleep(settings.EXECUTION_LOOP_SLEEP)
                    continue

                cycle = self.build_cycle_context()
                self.run_cycle(cycle)

                time.sleep(settings.EXECUTION_LOOP_SLEEP)

            except Exception as e:
                log.error("execution_controller_error", error=str(e))
                time.sleep(1)
