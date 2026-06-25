from survey_finder.coordination.lease import RedisLeaseProvider

def test_no_split_brain():
    a = RedisLeaseProvider()
    b = RedisLeaseProvider()

    a.try_acquire()
    b.try_acquire()

    # only one leader allowed
    assert not (a.is_leader() and b.is_leader())
