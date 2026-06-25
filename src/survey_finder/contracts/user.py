from pydantic import BaseModel

class UserProfile(BaseModel):
    user_id: str
    country: str
    min_hourly_rate: float = 15.0
    profile_version: str = "v1"
