import pytest
from survey_finder.adapters.base import BaseAdapter, AdapterConfig
from survey_finder.adapters.registry import AdapterRegistry
from survey_finder.adapters.errors import AdapterError, AdapterErrorType


class MockAdapter(BaseAdapter):
    async def initialize(self):
        self._is_initialized = True

    async def fetch_surveys(self, context):
        return []

    async def close(self):
        self._is_initialized = False


def test_adapter_registry():
    AdapterRegistry.register("mock", MockAdapter)
    assert "mock" in AdapterRegistry.list_sources()

    config = AdapterConfig(source="mock")
    adapter = AdapterRegistry.create_adapter("mock", config)
    assert adapter.source_name == "mock"
