import pytest
from survey_finder.buffer.queue import RedisBuffer
from survey_finder.buffer.backpressure import BackpressureController


def test_buffer():
    buffer = RedisBuffer(max_size=10)
    buffer.clear()

    assert buffer.push({"test": "data"})
    assert buffer.size() == 1

    event = buffer.pop()
    assert event is not None
    assert "queued_at" in event
    assert event.get("test") == "data"


def test_backpressure():
    buffer = RedisBuffer(max_size=10)
    buffer.clear()
    controller = BackpressureController(buffer, slow_threshold=0.7, full_threshold=0.9)

    # Fill buffer
    for i in range(9):
        buffer.push({"i": i})

    state = controller.check()
    assert state.signal == "ok"

    buffer.push({"i": 9})
    state = controller.check()
    assert state.signal == "full"

    buffer.clear()
