import pytest
from datetime import datetime
from survey_finder.normalization.engine import NormalizationEngine
from survey_finder.normalization.models import RawPayload


def test_normalization_valid():
    engine = NormalizationEngine()
    raw = RawPayload(
        payload_id="1",
        source="prolific",
        fetched_at=datetime.utcnow(),
        source_schema_version="v1",
        raw_content={
            "id": "123",
            "title": "Test Survey",
            "payout": 5.0,
            "duration_minutes": 10,
            "source": "prolific"
        }
    )
    result = engine.normalize(raw, "cycle-1")
    assert result.status.value == "valid"
    assert result.validated_survey is not None
    assert len(result.validation_errors) == 0


def test_normalization_missing_fields():
    engine = NormalizationEngine(strict=False)
    raw = RawPayload(
        payload_id="1",
        source="prolific",
        fetched_at=datetime.utcnow(),
        source_schema_version="v1",
        raw_content={
            "id": "123",
            "title": "Test Survey"
        }
    )
    result = engine.normalize(raw, "cycle-1")
    assert result.status.value == "valid"
    # Should have defaults applied
    assert result.validated_survey.get("payout") == 0.0
