from typing import List
from uuid import uuid4
from datetime import datetime, timezone

from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.contracts.cycle import CycleContext
from survey_finder.filter.rules import FilterRules, FilterResult  # noqa: F401

# FilterResult re-exported from here for backward-compat
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)

# Weighted rules — sum = 1.0
RULE_WEIGHTS = {
    "hourly_rate_ok":     0.40,  # financial — most critical
    "country_match":      0.30,  # eligibility gatekeeper (hard fail on mismatch)
    "device_compatible":  0.20,  # practical constraint
    "screening_required": 0.10,  # soft filter
}


class FilterEngine:
    """Evaluates survey eligibility with weighted scoring."""

    def __init__(self, min_score: float = 0.5):
        self.min_score = min_score
        self.rules = FilterRules()

    def evaluate(
        self,
        survey: Survey,
        profile: UserProfile,
        context: CycleContext,
    ) -> FilterResult:
        logger.info("filter_start", cycle_id=context.cycle_id, survey_id=survey.id)

        reasons: List[str] = []
        weighted_score: float = 0.0
        hard_fail: bool = False

        checks = [
            ("hourly_rate_ok",     lambda: self.rules.hourly_rate_ok(survey, profile)),
            ("country_match",      lambda: self.rules.country_match(survey, profile)),
            ("device_compatible",  lambda: self.rules.device_compatible(survey, profile)),
            ("screening_required", lambda: self.rules.screening_required(survey, profile)),
        ]

        for name, fn in checks:
            weight = RULE_WEIGHTS[name]
            passed, reason = fn()
            if passed:
                weighted_score += weight
                reasons.append(reason)
            else:
                reasons.append(f"FAIL:{reason}")
                if name == "country_match":
                    hard_fail = True  # country mismatch = instant reject

        # Also reject if source not in preferred_sources (when configured)
        if profile.preferred_sources and survey.source not in profile.preferred_sources:
            hard_fail = True
            reasons.append(f"FAIL:source_not_preferred:{survey.source}")

        # Also reject if duration exceeds user limit
        if profile.max_duration_minutes and survey.duration_minutes > profile.max_duration_minutes:
            weighted_score = max(0.0, weighted_score - 0.2)
            reasons.append(f"FAIL:duration_too_long:{survey.duration_minutes}min")

        if hard_fail:
            status = "REJECTED"
            weighted_score = 0.0
        elif weighted_score >= self.min_score:
            status = "ELIGIBLE"
        elif weighted_score > 0.15:
            status = "REVIEW"
        else:
            status = "REJECTED"

        result = FilterResult(
            decision_id=str(uuid4()),
            cycle_id=context.cycle_id,
            survey_id=survey.id,
            status=status,
            score=round(weighted_score, 4),
            reasons=reasons,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "filter_complete",
            cycle_id=context.cycle_id,
            survey_id=survey.id,
            status=status,
            score=weighted_score,
        )
        return result