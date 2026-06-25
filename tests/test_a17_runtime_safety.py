from survey_finder.runtime.dlq import DeadLetterQueue
from survey_finder.runtime.schema_validator import SchemaValidator
from survey_finder.runtime.circuit_breaker import CircuitBreaker
from survey_finder.adapters.wrapped import SafeAdapterWrapper

class BadAdapter:
    def fetch(self, cycle):
        return [
            "invalid",
            {"source": "x", "schema_version": "1", "payload": {}},
            {"bad": "schema"}
        ]

def test_dlq_and_validation():
    dlq = DeadLetterQueue()
    validator = SchemaValidator(dlq)
    breaker = CircuitBreaker(failure_threshold=2)

    wrapper = SafeAdapterWrapper(BadAdapter(), validator, breaker)

    res = wrapper.fetch(type("C", (), {"cycle_id": "c1"})())

    assert isinstance(res, list)
    assert dlq.size() >= 1

def test_circuit_breaker():
    breaker = CircuitBreaker(failure_threshold=1)

    assert breaker.allow() is True
    breaker.failure()
    assert breaker.allow() is False
