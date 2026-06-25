import pytest
from survey_finder.adapters.prolific.adapter import ProlificAdapter
from survey_finder.adapters.base import AdapterConfig
from survey_finder.contracts.cycle import CycleContext


@pytest.mark.asyncio
async def test_prolific_adapter():
    config = AdapterConfig(source="prolific", timeout_seconds=10)
    adapter = ProlificAdapter(config)

    await adapter.initialize()
    assert adapter._is_initialized

    context = CycleContext()
    result = await adapter.fetch_surveys(context)
    assert result.source == "prolific"

    await adapter.close()
