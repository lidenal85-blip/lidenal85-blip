from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4
from .versioning import CURRENT_CONTRACT_VERSION

class CycleContext(BaseModel):
    cycle_id: str = str(uuid4())
    version: str = CURRENT_CONTRACT_VERSION.value
    started_at: datetime = datetime.utcnow()
    status: str = "running"
