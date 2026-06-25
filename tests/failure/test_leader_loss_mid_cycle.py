import time
from survey_finder.coordination.leader import LeaderElectionService
from survey_finder.runtime.execution_controller import ExecutionController

def test_leader_loss_handling():
    leader = LeaderElectionService()
    controller = ExecutionController(leader)

    leader.start()

    # simulate run loop iteration safety
    for _ in range(5):
        if leader.is_leader():
            cycle = controller.build_cycle_context()
            assert cycle.cycle_id is not None
        time.sleep(0.1)
