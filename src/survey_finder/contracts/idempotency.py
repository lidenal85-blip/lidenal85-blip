from pydantic import BaseModel
from datetime import datetime

class IdempotencyKey(BaseModel):
    key: str
    entity_type: str
    created_at: datetime
