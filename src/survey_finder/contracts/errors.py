from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class ErrorType(str, Enum):
    ADAPTER_TIMEOUT = "adapter_timeout"
    ADAPTER_CAPTCHA = "adapter_captcha"
    SCHEMA_DRIFT = "schema_drift"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    EXTERNAL_RATE_LIMIT = "external_rate_limit"
    INTERNAL_FAILURE = "internal_failure"

class ErrorEvent(BaseModel):
    cycle_id: str
    source: str
    error_type: ErrorType
    message: str
    timestamp: datetime
    retryable: bool = True
