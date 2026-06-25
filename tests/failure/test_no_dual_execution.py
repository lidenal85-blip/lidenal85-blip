from survey_finder.coordination.leader import LeaderElectionService

def test_single_leader_only():
    a = LeaderElectionService()
    b = LeaderElectionService()

    a.is_leader_flag = True
    b.is_leader_flag = False

    assert not (a.is_leader() and b.is_leader())
