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

def test_cycle_replay_and_metrics():
    orch = Orchestrator(
        adapters=[DummyAdapter()],
        buffer=EventBuffer(),
        idempotency=IdempotencyGate(),
        filter_engine=FilterEngine(),
        dispatcher=DummyDispatcher()
    )

    profile = UserProfile(user_id="u1", country="US", min_hourly_rate=1)
    cycle = type("C", (), {"cycle_id": "c1"})()

    orch.run_cycle(cycle, profile)

    assert orch.metrics.snapshot()["cycles_started"] == 1
    assert len(orch.replay.get("c1")) > 0
