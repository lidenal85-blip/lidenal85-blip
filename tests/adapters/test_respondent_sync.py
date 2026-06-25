import pytest
from survey_finder.adapters.respondent.adapter import RespondentAdapter
from survey_finder.adapters.base import AdapterConfig


def test_respondent_adapter_creation():
    """Test RespondentAdapter can be instantiated."""
    config = AdapterConfig(source="respondent", timeout_seconds=10)
    adapter = RespondentAdapter(config)
    assert adapter.config.source == "respondent"
