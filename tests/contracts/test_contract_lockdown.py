from survey_finder.contracts.cep import CycleExecutionProtocol
from survey_finder.contracts.errors import ErrorEvent, ErrorType
from survey_finder.contracts.dlq import DLQItem
from survey_finder.contracts.survey import Survey

def test_cycle_protocol():
    c = CycleExecutionProtocol()
    assert c.status == "running"
    c.mark_finished()
    assert c.status == "finished"

def test_error_event():
    e = ErrorEvent(
        cycle_id="1",
        source="adapter",
        error_type=ErrorType.ADAPTER_TIMEOUT,
        message="timeout",
        timestamp="2024-01-01T00:00:00"
    )
    assert e.source == "adapter"

def test_dlq_item():
    d = DLQItem(
        cycle_id="1",
        source="adapter",
        payload_type="survey",
        raw_payload={"id": "x"},
        reason="schema_error",
        failed_at="2024-01-01T00:00:00"
    )
    assert d.source == "adapter"

def test_survey_versioning():
    s = Survey(
        id="1",
        title="test",
        payout=10.0,
        duration_minutes=5,
        source="prolific"
    )
    assert s.schema_version == "v1"
