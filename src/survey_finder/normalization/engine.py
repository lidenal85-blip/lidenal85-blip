from typing import Dict, Any, Optional, List

from survey_finder.normalization.models import NormalizationResult, NormalizationStatus, RawPayload
from survey_finder.normalization.schema import SchemaValidator
from survey_finder.contracts.survey import Survey
from survey_finder.contracts.dlq import DLQItem
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class NormalizationEngine:
    """Normalizes raw survey data into validated SurveyDTOs."""

    def __init__(self, strict: bool = True):
        self.validator = SchemaValidator(strict=strict)

    def normalize(
        self,
        raw_payload: RawPayload,
        cycle_id: str
    ) -> NormalizationResult:
        """
        Normalize raw payload to survey DTO.

        Returns:
            NormalizationResult with status and validated_survey
        """
        logger.info(
            "normalization_start",
            cycle_id=cycle_id,
            source=raw_payload.source,
            payload_id=raw_payload.payload_id
        )

        raw_data = raw_payload.raw_content
        warnings: List[str] = []

        # Step 1: Normalize field names
        normalized_data = self._normalize_fields(raw_data)

        # Step 2: Handle missing fields with defaults
        normalized_data = self._apply_defaults(normalized_data)

        # Step 3: Validate
        is_valid, errors, survey = self.validator.validate(normalized_data)

        if not is_valid:
            logger.warning(
                "normalization_failed",
                cycle_id=cycle_id,
                errors=errors,
                payload_id=raw_payload.payload_id
            )

            return NormalizationResult(
                status=NormalizationStatus.INVALID,
                validation_errors=errors,
                warnings=warnings
            )

        # Step 4: Add source metadata
        if survey:
            # Check for data quality issues
            if survey.payout <= 0:
                warnings.append("Payout is zero or negative")
            if survey.duration_minutes <= 0:
                warnings.append("Duration is zero or negative")

            # Partial validation: warnings but still valid
            if warnings and self.validator.strict:
                return NormalizationResult(
                    status=NormalizationStatus.PARTIAL,
                    validated_survey=survey.model_dump(),
                    validation_errors=[],
                    warnings=warnings
                )

            return NormalizationResult(
                status=NormalizationStatus.VALID,
                validated_survey=survey.model_dump(),
                validation_errors=[],
                warnings=warnings
            )

        return NormalizationResult(
            status=NormalizationStatus.INVALID,
            validation_errors=["Survey creation failed"]
        )

    def _normalize_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field names."""
        field_mappings = {
            "survey_id": "id",
            "study_id": "id",
            "name": "title",
            "compensation": "payout",
            "reward": "payout",
            "duration": "duration_minutes",
            "time": "duration_minutes",
            "platform": "source"
        }

        normalized = data.copy()
        for old_key, new_key in field_mappings.items():
            if old_key in normalized and new_key not in normalized:
                normalized[new_key] = normalized[old_key]

        return normalized

    def _apply_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing fields."""
        defaults = {
            "id": "",
            "title": "Untitled Survey",
            "payout": 0.0,
            "duration_minutes": 0,
            "source": "unknown",
            "schema_version": "v1"
        }

        for key, default_value in defaults.items():
            if key not in data or data[key] is None:
                data[key] = default_value

        return data

    def create_dlq_item(
        self,
        raw_payload: RawPayload,
        cycle_id: str,
        reason: str
    ) -> DLQItem:
        """Create a DLQ item for failed normalization."""
        return DLQItem(
            cycle_id=cycle_id,
            source=raw_payload.source,
            payload_type="survey",
            raw_payload=raw_payload.raw_content,
            reason=reason,
            failed_at=datetime.utcnow()
        )
