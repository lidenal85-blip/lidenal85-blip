from survey_finder.runtime.event_buffer import EventBuffer
from survey_finder.runtime.shutdown import ShutdownController
from survey_finder.runtime.idempotency import IdempotencyGate
from survey_finder.filter.engine import FilterEngine

class DummyAdapter:
    def fetch(self, cycle):
        return []

class DummyDispatcher:
    def send(self, x):
        pass

def test_shutdown_flow():
    buffer = EventBuffer(max_size=2)
    shutdown = ShutdownController()

    shutdown.initiate_shutdown()
    assert shutdown.is_shutdown() is True

def test_backpressure_trigger():
    buffer = EventBuffer(max_size=1)

    buffer.push("a")
    try:
        buffer.push("b")
        assert False
    except RuntimeError as e:
        assert "BACKPRESSURE" in str(e)
