from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
from .versioning import CURRENT_CONTRACT_VERSION

class CycleExecutionProtocol(BaseModel):
    """
    Single source of truth for execution lifecycle.
    """
    cycle_id: str = Field(default_factory=lambda: str(uuid4()))
    version: str = CURRENT_CONTRACT_VERSION.value
    started_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "running"

    def mark_finished(self):
        self.status = "finished"

    def mark_failed(self):
        self.status = "failed"
