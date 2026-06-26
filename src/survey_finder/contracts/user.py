from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class UserProfile(BaseModel):
    user_id: str
    country: str = "US"
    min_hourly_rate: float = 15.0
    # --- NEW fields ---
    allowed_devices: List[str] = ["desktop", "mobile", "tablet"]
    demographics: Dict[str, Any] = {}  # age, gender, occupation, etc.
    preferred_sources: List[str] = []  # empty = all sources
    max_duration_minutes: Optional[int] = None  # None = no limit
    notifications_enabled: bool = True
    # ---
    profile_version: str = "v1"
