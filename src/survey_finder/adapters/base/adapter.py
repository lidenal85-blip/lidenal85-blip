from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

from survey_finder.contracts.survey import Survey
from survey_finder.contracts.cycle import CycleContext
from survey_finder.adapters.errors import AdapterError, AdapterErrorType


class AdapterConfig(BaseModel):
    source: str
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 5
    rate_limit_per_minute: Optional[int] = None
    use_proxy: bool = False


class AdapterResult(BaseModel):
    source: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    surveys: List[Survey] = []
    errors: List[Dict[str, Any]] = []
    total_fetched: int = 0


class BaseAdapter(ABC):
    """Base class for all survey source adapters."""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self._session = None
        self._is_initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize adapter (login, setup session, etc.)"""
        pass

    @abstractmethod
    async def fetch_surveys(self, context: CycleContext) -> AdapterResult:
        """Fetch surveys from source."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close adapter resources."""
        pass

    @property
    def source_name(self) -> str:
        return self.config.source

    def _create_error(self, error_type: AdapterErrorType, message: str, retryable: bool = True) -> AdapterError:
        return AdapterError(
            error_type=error_type,
            message=message,
            source=self.source_name,
            retryable=retryable
        )
