from survey_finder.coordination.leader import LeaderElectionService

_leader_service = None

def get_leader_service():
    global _leader_service
    if _leader_service is None:
        _leader_service = LeaderElectionService()
    return _leader_service
