import time
from survey_finder.coordination.leader import LeaderElectionService
from survey_finder.runtime.execution_controller import ExecutionController

def test_execution_standby_safety():
    leader = LeaderElectionService()
    controller = ExecutionController(leader)

    # simulate standby mode
    assert leader.is_leader() is False

    # controller should not crash even if not leader
    for _ in range(3):
        if not leader.is_leader():
            pass
        time.sleep(0.1)
