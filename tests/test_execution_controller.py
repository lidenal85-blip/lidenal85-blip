from survey_finder.runtime.execution_controller import ExecutionController
from survey_finder.runtime.lease import LeaseLock
from survey_finder.runtime.orchestrator import Orchestrator
from survey_finder.runtime.event_buffer import EventBuffer
from survey_finder.runtime.idempotency import IdempotencyGate
from survey_finder.filter.engine import FilterEngine
from survey_finder.contracts.user import UserProfile

class DummyAdapter:
    def fetch(self, cycle):
        return []

class DummyDispatcher:
    def send(self, x):
        pass

def test_lease_blocks_double_execution():
    lease = LeaseLock(ttl_seconds=10)

    orch = Orchestrator(
        adapters=[DummyAdapter()],
        buffer=EventBuffer(),
        idempotency=IdempotencyGate(),
        filter_engine=FilterEngine(),
        dispatcher=DummyDispatcher()
    )

    controller = ExecutionController(orch, lease)

    profile = UserProfile(user_id="u1", country="US", min_hourly_rate=1)
    cycle = type("C", (), {"cycle_id": "c1"})()

    r1 = controller.run(cycle, profile)
    r2 = controller.run(cycle, profile)

    assert r1.status in ("success", "failed")
    assert r2.status.startswith("rejected")
