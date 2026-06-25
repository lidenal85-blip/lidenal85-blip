import pytest
from survey_finder.idempotency.gate import RedisIdempotencyGate


def test_idempotency_gate():
    gate = RedisIdempotencyGate(ttl_seconds=60)
    key = "test:123"

    # First check should be accepted
    result1 = gate.check_and_set(key)
    assert result1.status == "ACCEPTED"

    # Second check should be duplicate
    result2 = gate.check_and_set(key)
    assert result2.status == "DUPLICATE"

    # Cleanup
    gate.clear(key)
    assert not gate.exists(key)
