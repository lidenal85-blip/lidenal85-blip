from pydantic import BaseModel

class Survey(BaseModel):
    id: str
    title: str
    payout: float
    duration_minutes: int
    source: str
    schema_version: str = "v1"
