from survey_finder.domain.filtering.engine import FilterEngine
from survey_finder.domain.normalization.models import NormalizedSurvey

def test_filter():
    f = FilterEngine(min_hourly_rate=15)

    survey = NormalizedSurvey(
        id="1",
        title="t",
        payout=10.0,
        duration_minutes=60,
        source="x",
        cycle_id="c1"
    )

    assert isinstance(f.filter([survey]), list)
