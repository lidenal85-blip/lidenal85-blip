from survey_finder.contracts.survey import Survey
def test_survey_contract():
    s = Survey(
        id="1",
        title="test",
        payout=10.0,
        duration_minutes=5,
        source="prolific"
    )
    assert s.id == "1"
