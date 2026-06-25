from survey_finder.adapters.registry.registry import AdapterRegistry

def test_registry():
    r = AdapterRegistry()
    assert len(r.all()) >= 3
