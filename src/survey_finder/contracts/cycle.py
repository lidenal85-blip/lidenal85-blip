from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4
class CycleContext(BaseModel):
    cycle_id: str = str(uuid4())
    started_at: datetime = datetime.utcnow()
