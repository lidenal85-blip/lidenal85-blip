from enum import Enum
from typing import Optional


class AdapterErrorType(str, Enum):
    TIMEOUT = "timeout"
    CAPTCHA = "captcha"
    LOGIN_FAILED = "login_failed"
    RATE_LIMIT = "rate_limit"
    PARSE_ERROR = "parse_error"
    NETWORK = "network"
    AUTH_FAILED = "auth_failed"
    NOT_FOUND = "not_found"
    INTERNAL = "internal"


class AdapterError(Exception):
    def __init__(
        self,
        error_type: AdapterErrorType,
        message: str,
        source: Optional[str] = None,
        retryable: bool = True,
        cause: Optional[Exception] = None
    ):
        self.error_type = error_type
        self.message = message
        self.source = source
        self.retryable = retryable
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.error_type}] {self.message}"
