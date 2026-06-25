from pydantic import BaseModel

class NormalizedSurvey(BaseModel):
    id: str
    title: str
    payout: float
    duration_minutes: int
    source: str
    cycle_id: str
