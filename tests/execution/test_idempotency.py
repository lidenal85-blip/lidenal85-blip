from survey_finder.execution.idempotency.gate import IdempotencyGate

def test_idempotency():
    g = IdempotencyGate()

    assert g.check_and_set("x") is True
    assert g.check_and_set("x") is False
