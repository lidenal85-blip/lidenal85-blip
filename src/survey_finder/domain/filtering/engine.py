from typing import List
from survey_finder.domain.normalization.models import NormalizedSurvey

class FilterEngine:
    """
    Deterministic eligibility filter.
    No side effects. Stateless.
    """

    def __init__(self, min_hourly_rate: float = 15.0):
        self.min_hourly_rate = min_hourly_rate

    def _hourly_rate(self, survey: NormalizedSurvey) -> float:
        hours = max(survey.duration_minutes / 60.0, 0.01)
        return survey.payout / hours

    def is_eligible(self, survey: NormalizedSurvey) -> bool:
        return self._hourly_rate(survey) >= self.min_hourly_rate

    def filter(self, surveys: List[NormalizedSurvey]) -> List[NormalizedSurvey]:
        return [s for s in surveys if self.is_eligible(s)]
