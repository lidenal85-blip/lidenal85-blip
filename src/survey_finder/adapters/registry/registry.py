from typing import List
from survey_finder.adapters.prolific.adapter import ProlificAdapter
from survey_finder.adapters.cloudresearch.adapter import CloudResearchAdapter
from survey_finder.adapters.respondent.adapter import RespondentAdapter

class AdapterRegistry:
    """
    Central registry of all adapters.
    """

    def __init__(self):
        self._adapters = [
            ProlificAdapter(),
            CloudResearchAdapter(),
            RespondentAdapter()
        ]

    def all(self) -> List:
        return self._adapters
