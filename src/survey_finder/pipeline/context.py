from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

from survey_finder.contracts.cycle import CycleContext
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.user import UserProfile
from survey_finder.normalization.models import RawPayload, NormalizationResult
from survey_finder.filter.engine import FilterResult


@dataclass
class PipelineContext:
    """Context passed through pipeline steps."""
    
    cycle_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    
    # Input
    raw_payload: Optional[RawPayload] = None
    user_profile: Optional[UserProfile] = None
    
    # Step results
    normalization_result: Optional[NormalizationResult] = None
    survey: Optional[Survey] = None
    filter_result: Optional[FilterResult] = None
    
    # Output
    delivered: bool = False
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_error(self, step: str, error: str, retryable: bool = True) -> None:
        self.errors.append({
            "step": step,
            "error": error,
            "retryable": retryable,
            "timestamp": datetime.utcnow().isoformat()
        })
