from survey_finder.execution.buffer.event_buffer import BackpressureBuffer

def test_buffer():
    b = BackpressureBuffer(max_size=2)

    assert b.push({"a": 1})
    assert b.push({"b": 2})
    assert b.push({"c": 3}) is False
