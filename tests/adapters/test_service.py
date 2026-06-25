from survey_finder.adapters.registry.service import AdapterService

def test_service_runs():
    s = AdapterService()
    result = s.fetch_all("cycle_test", {"country": "NL"})
    assert isinstance(result, list)
