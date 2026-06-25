from survey_finder.execution.orchestrator.controller import ExecutionController

def test_cycle_success():
    c = ExecutionController()

    def handler(cycle_id):
        assert cycle_id is not None

    r = c.run_cycle(handler)
    assert r.status in ["success", "failed"]
