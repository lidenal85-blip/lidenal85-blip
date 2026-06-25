import pytest
from survey_finder.idempotency.gate import RedisIdempotencyGate
from survey_finder.buffer.queue import RedisBuffer


def test_idempotency_gate():
    gate = RedisIdempotencyGate(ttl_seconds=60)
    key = "test:123"
    result1 = gate.check_and_set(key)
    assert result1.status == "ACCEPTED"
    result2 = gate.check_and_set(key)
    assert result2.status == "DUPLICATE"
    gate.clear(key)
    assert not gate.exists(key)


def test_buffer():
    buffer = RedisBuffer(max_size=10)
    buffer.clear()
    assert buffer.push({"test": "data"})
    assert buffer.size() == 1
    event = buffer.pop()
    assert event is not None
    buffer.clear()
