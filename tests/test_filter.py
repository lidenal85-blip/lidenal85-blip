import pytest
from survey_finder.filter.engine import FilterEngine
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.contracts.cycle import CycleContext


def test_filter_eligible():
    engine = FilterEngine(min_score=0.5)
    survey = Survey(
        id="1",
        title="Test",
        payout=10.0,
        duration_minutes=10,
        source="prolific"
    )
    profile = UserProfile(
        user_id="user1",
        country="US",
        min_hourly_rate=15.0
    )
    context = CycleContext()

    result = engine.evaluate(survey, profile, context)
    assert result.status == "ELIGIBLE"
    assert result.score >= 0.5
