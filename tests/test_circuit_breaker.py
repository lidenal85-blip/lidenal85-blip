import pytest
import time
from survey_finder.hardening.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState


def test_circuit_breaker_closed():
    cb = CircuitBreaker("test")
    assert cb.state == CircuitState.CLOSED
    
    def success():
        return "ok"
    
    result = cb.call(success)
    assert result == "ok"


def test_circuit_breaker_opens_on_failure():
    config = CircuitBreakerConfig(failure_threshold=2)
    cb = CircuitBreaker("test", config)
    
    def fail():
        raise ValueError("test error")
    
    # First failure
    with pytest.raises(ValueError):
        cb.call(fail)
    assert cb.state == CircuitState.CLOSED
    
    # Second failure - should open
    with pytest.raises(ValueError):
        cb.call(fail)
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_reset():
    cb = CircuitBreaker("test")
    cb.reset()
    assert cb.state == CircuitState.CLOSED
