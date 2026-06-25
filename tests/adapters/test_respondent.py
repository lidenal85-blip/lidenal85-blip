import pytest
from survey_finder.adapters.respondent.adapter import RespondentAdapter
from survey_finder.adapters.base import AdapterConfig
from survey_finder.contracts.cycle import CycleContext


@pytest.mark.asyncio
async def test_respondent_adapter():
    config = AdapterConfig(source="respondent", timeout_seconds=10)
    adapter = RespondentAdapter(config)

    await adapter.initialize()
    assert adapter._is_initialized

    context = CycleContext()
    result = await adapter.fetch_surveys(context)
    assert result.source == "respondent"

    await adapter.close()
