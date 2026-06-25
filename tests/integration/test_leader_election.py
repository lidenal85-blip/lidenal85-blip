import time
from survey_finder.coordination.lease import RedisLeaseProvider

def test_leader_acquisition():
    a = RedisLeaseProvider()
    b = RedisLeaseProvider()

    assert a.try_acquire() is True
    assert b.try_acquire() in [False, None]

def test_lease_renewal():
    a = RedisLeaseProvider()
    assert a.try_acquire() is True
    assert a.renew() is True
