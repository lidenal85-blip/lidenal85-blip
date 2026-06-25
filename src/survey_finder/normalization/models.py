from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from survey_finder.contracts.versioning import CURRENT_CONTRACT_VERSION


class NormalizationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"


class NormalizationResult(BaseModel):
    status: NormalizationStatus
    validated_survey: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = []
    warnings: List[str] = []
    normalized_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = CURRENT_CONTRACT_VERSION.value


class RawPayload(BaseModel):
    payload_id: str
    source: str
    fetched_at: datetime
    source_schema_version: str
    raw_content: Dict[str, Any]
    metadata: Dict[str, Any] = {}
