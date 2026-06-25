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
    status: str  # ELIGIBLE, REJECTED, REVIEW
    score: float = 0.0
    reasons: List[str] = []
    generated_at: str


class FilterRules:
    """Collection of filter rules for survey eligibility."""

    @staticmethod
    def country_match(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        """Check if user's country matches survey requirements."""
        survey_country = getattr(survey, "country", None)
        if not survey_country:
            return True, "no_country_restriction"

        if survey_country == profile.country:
            return True, "country_match"
        return False, "country_mismatch"

    @staticmethod
    def hourly_rate_ok(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        """Check if survey meets minimum hourly rate."""
        if survey.payout <= 0 or survey.duration_minutes <= 0:
            return False, "invalid_payout_or_duration"

        hourly_rate = (survey.payout / survey.duration_minutes) * 60
        if hourly_rate >= profile.min_hourly_rate:
            return True, "hourly_rate_ok"
        return False, "hourly_rate_too_low"

    @staticmethod
    def device_compatible(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        """Check if user's device is compatible."""
        allowed_devices = getattr(profile, "allowed_devices", [])
        if not allowed_devices:
            return True, "no_device_restriction"

        survey_device = getattr(survey, "device_rules", [])
        if not survey_device:
            return True, "no_device_restriction"

        if any(device in survey_device for device in allowed_devices):
            return True, "device_match"
        return False, "device_mismatch"

    @staticmethod
    def screening_required(survey: Survey, profile: UserProfile) -> tuple[bool, str]:
        """Check if user meets screening requirements."""
        screening_required = getattr(survey, "screening_required", False)
        if not screening_required:
            return True, "no_screening_required"

        demographics = getattr(profile, "demographics", {})
        if demographics:
            return True, "screening_requirements_met"
        return False, "screening_requirements_not_met"
