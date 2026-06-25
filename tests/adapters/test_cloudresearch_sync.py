import pytest
from survey_finder.adapters.cloudresearch.adapter import CloudResearchAdapter
from survey_finder.adapters.base import AdapterConfig


def test_cloudresearch_adapter_creation():
    """Test CloudResearchAdapter can be instantiated."""
    config = AdapterConfig(source="cloudresearch", timeout_seconds=10)
    adapter = CloudResearchAdapter(config)
    assert adapter.config.source == "cloudresearch"
