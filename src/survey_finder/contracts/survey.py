from typing import Optional, List
from pydantic import BaseModel

class Survey(BaseModel):
    id: str
    title: str
    payout: float
    duration_minutes: int
    source: str
    # --- NEW fields ---
    url: str = ""                          # direct link (required for notification)
    description: str = ""
    places_available: Optional[int] = None # None = unlimited
    deadline: Optional[str] = None         # ISO datetime string
    device_requirements: List[str] = []    # ["desktop", "mobile", "tablet"]
    eligibility_criteria: dict = {}        # raw criteria from platform
    country: Optional[str] = None          # restriction (None = any)
    # ---
    schema_version: str = "v1"

    @property
    def hourly_rate(self) -> float:
        if self.duration_minutes <= 0:
            return 0.0
        return (self.payout / self.duration_minutes) * 60
