from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile


class FilterRule(BaseModel):
    name: str
    description: str
    required: bool = True


class FilterResult(BaseModel):
    decision_id: str
    cycle_id: str
    survey_id: str
    status: str   # ELIGIBLE | REJECTED | REVIEW
    score: float = 0.0
    reasons: List[str] = []
    generated_at: str


class FilterRules:
    """Collection of filter rules."""

    @staticmethod
    def country_match(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        if not survey.country:
            return True, "no_country_restriction"
        if survey.country.upper() == profile.country.upper():
            return True, "country_match"
        return False, f"country_mismatch:{survey.country}!={profile.country}"

    @staticmethod
    def hourly_rate_ok(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        if survey.payout <= 0 or survey.duration_minutes <= 0:
            return False, "invalid_payout_or_duration"
        hourly = (survey.payout / survey.duration_minutes) * 60
        if hourly >= profile.min_hourly_rate:
            return True, f"hourly_rate_ok:{hourly:.2f}/hr"
        return False, f"hourly_rate_too_low:{hourly:.2f}<{profile.min_hourly_rate}"

    @staticmethod
    def device_compatible(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        survey_devices = survey.device_requirements
        if not survey_devices:
            return True, "no_device_restriction"
        if not profile.allowed_devices:
            return True, "no_device_preference"
        if any(d in survey_devices for d in profile.allowed_devices):
            return True, "device_match"
        return False, f"device_mismatch:{survey_devices}"

    @staticmethod
    def screening_required(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        criteria = survey.eligibility_criteria
        if not criteria:
            return True, "no_screening_required"
        if profile.demographics:
            return True, "demographics_available"
        return False, "screening_required_but_no_demographics"