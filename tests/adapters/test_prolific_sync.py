import pytest
from survey_finder.adapters.prolific.adapter import ProlificAdapter
from survey_finder.adapters.base import AdapterConfig


def test_prolific_adapter_creation():
    """Test ProlificAdapter can be instantiated."""
    config = AdapterConfig(source="prolific", timeout_seconds=10)
    adapter = ProlificAdapter(config)
    assert adapter.config.source == "prolific"
    assert adapter.base_url == "https://www.prolific.com"
