from dataclasses import dataclass
from survey_finder.contracts.cycle import CycleContext
from survey_finder.runtime.lease import LeaseLock

@dataclass
class ExecutionResult:
    cycle_id: str
    status: str
    processed_items: int

class ExecutionController:
    def __init__(self, orchestrator, lease: LeaseLock):
        self.orchestrator = orchestrator
        self.lease = lease

    def run(self, cycle: CycleContext, profile) -> ExecutionResult:
        if not self.lease.acquire(cycle.cycle_id):
            return ExecutionResult(
                cycle_id=cycle.cycle_id,
                status="rejected: lease_active",
                processed_items=0
            )

        processed = 0

        try:
            self.lease.heartbeat()

            self.orchestrator.run_cycle(cycle, profile)
            processed = 1

            self.lease.release()

            return ExecutionResult(
                cycle_id=cycle.cycle_id,
                status="success",
                processed_items=processed
            )

        except Exception:
            self.lease.release()
            return ExecutionResult(
                cycle_id=cycle.cycle_id,
                status="failed",
                processed_items=processed
            )
