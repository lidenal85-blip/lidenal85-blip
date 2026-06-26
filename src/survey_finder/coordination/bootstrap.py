import uuid
from survey_finder.coordination.leader import LeaderElectionService
from survey_finder.coordination.lease import LeaseManager

_leader_service = None

def get_leader_service() -> LeaderElectionService:
    global _leader_service
    if _leader_service is None:
        lease_manager = LeaseManager(ttl_seconds=30)
        service_id = str(uuid.uuid4())
        _leader_service = LeaderElectionService(
            lease_manager=lease_manager,
            service_id=service_id,
            ttl_seconds=30,
        )
    return _leader_service
