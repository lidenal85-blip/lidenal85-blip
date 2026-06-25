from survey_finder.adapters.base import BaseAdapter, AdapterConfig, AdapterResult
from survey_finder.adapters.registry import AdapterRegistry, AdapterService
from survey_finder.adapters.errors import AdapterError, AdapterErrorType

# Import adapters for registration
from survey_finder.adapters.prolific.adapter import ProlificAdapter
from survey_finder.adapters.cloudresearch.adapter import CloudResearchAdapter
from survey_finder.adapters.respondent.adapter import RespondentAdapter

# Auto-register adapters
AdapterRegistry.register("prolific", ProlificAdapter)
AdapterRegistry.register("cloudresearch", CloudResearchAdapter)
AdapterRegistry.register("respondent", RespondentAdapter)
