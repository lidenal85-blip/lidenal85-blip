from typing import List, Dict, Any, Tuple, Optional
from uuid import uuid4
from datetime import datetime

from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.contracts.cycle import CycleContext
from survey_finder.filter.rules import FilterRules, FilterResult
from survey_finder.logging.logger import init_logger

logger = init_logger()


class FilterEngine:
    """Evaluates survey eligibility based on user profile."""

    def __init__(self, min_score: float = 0.5):
        self.min_score = min_score
        self.rules = FilterRules()

    def evaluate(
        self,
        survey: Survey,
        profile: UserProfile,
        context: CycleContext
    ) -> FilterResult:
        """
        Evaluate a survey against user profile.

        Returns:
            FilterResult with decision
        """
        logger.info(
            "filter_start",
            cycle_id=context.cycle_id,
            survey_id=survey.id
        )

        reasons: List[str] = []
        passed_checks: int = 0
        total_checks: int = 0

        # Run all filters
        filters = [
            ("country_match", lambda: self.rules.country_match(survey, profile)),
            ("hourly_rate_ok", lambda: self.rules.hourly_rate_ok(survey, profile)),
            ("device_compatible", lambda: self.rules.device_compatible(survey, profile)),
            ("screening_required", lambda: self.rules.screening_required(survey, profile)),
        ]

        for name, filter_fn in filters:
            total_checks += 1
            passed, reason = filter_fn()
            if passed:
                passed_checks += 1
                reasons.append(reason)
            else:
                reasons.append(f"FAIL_{reason}")

        # Calculate score
        score = passed_checks / total_checks if total_checks > 0 else 0.0

        # Determine status
        if score >= self.min_score:
            status = "ELIGIBLE"
        elif score > 0:
            status = "REVIEW"
        else:
            status = "REJECTED"

        decision_id = str(uuid4())

        result = FilterResult(
            decision_id=decision_id,
            cycle_id=context.cycle_id,
            survey_id=survey.id,
            status=status,
            score=score,
            reasons=reasons,
            generated_at=datetime.utcnow().isoformat()
        )

        logger.info(
            "filter_complete",
            cycle_id=context.cycle_id,
            survey_id=survey.id,
            status=status,
            score=score
        )

        return result
