from survey_finder.domain.normalization.normalizer import SurveyNormalizer

def test_normalizer():
    n = SurveyNormalizer()

    raw = {
        "id": "1",
        "title": "test",
        "payout": 10.0,
        "duration_minutes": 10,
        "source": "prolific",
        "cycle_id": "c1"
    }

    out = n.normalize(raw)
    assert out.id == "1"
