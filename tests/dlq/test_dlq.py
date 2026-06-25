import pytest
from datetime import datetime
from survey_finder.contracts.dlq import DLQItem
from survey_finder.dlq.storage import DLQStorage


def test_dlq_item():
    item = DLQItem(
        cycle_id="c1",
        source="prolific",
        payload_type="survey",
        raw_payload={"id": "1"},
        reason="validation_failed",
        failed_at=datetime.utcnow()
    )
    assert item.cycle_id == "c1"
    assert item.source == "prolific"


def test_dlq_storage():
    storage = DLQStorage(ttl_seconds=60)
    item = DLQItem(
        cycle_id="c1",
        source="prolific",
        payload_type="survey",
        raw_payload={"id": "1"},
        reason="test",
        failed_at=datetime.utcnow()
    )
    storage.store(item)
    items = storage.fetch_by_cycle("c1")
    assert len(items) > 0
    assert items[0].cycle_id == "c1"
