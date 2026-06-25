import pytest
import time
from survey_finder.hardening.rate_limiter import RateLimiter, RateLimiterConfig


def test_rate_limiter_acquire():
    config = RateLimiterConfig(requests_per_minute=60, burst_size=10)
    limiter = RateLimiter("test", config)
    
    # Should be able to acquire multiple tokens
    for _ in range(5):
        assert limiter.acquire(tokens=1) is True


def test_rate_limiter_timeout():
    config = RateLimiterConfig(requests_per_minute=60, burst_size=1)
    limiter = RateLimiter("test", config)
    
    # Use the only token
    assert limiter.acquire(tokens=1) is True
    
    # Should fail immediately with timeout=0
    assert limiter.acquire(tokens=1, timeout=0.1) is False
