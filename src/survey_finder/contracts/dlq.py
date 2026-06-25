from pydantic import BaseModel
from datetime import datetime

class DLQItem(BaseModel):
    cycle_id: str
    source: str
    payload_type: str
    raw_payload: dict
    reason: str
    failed_at: datetime
