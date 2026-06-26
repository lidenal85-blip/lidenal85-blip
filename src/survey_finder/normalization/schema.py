from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError

from survey_finder.contracts.survey import Survey
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class SchemaValidator:
    """Validates survey data against schema."""

    def __init__(self, strict: bool = True):
        self.strict = strict

    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str], Optional[Survey]]:
        """
        Validate data against Survey schema.

        Returns:
            (is_valid, errors, survey)
        """
        errors: List[str] = []
        survey: Optional[Survey] = None

        try:
            # Validate required fields
            required = ["id", "title", "payout", "duration_minutes", "source"]
            for field in required:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {field}")

            if errors and self.strict:
                return False, errors, None

            # Try to create Survey
            survey = Survey(
                id=data.get("id", ""),
                title=data.get("title", ""),
                payout=float(data.get("payout", 0)),
                duration_minutes=int(data.get("duration_minutes", 0)),
                source=data.get("source", "unknown"),
                schema_version="v1"
            )

            return True, [], survey

        except (ValueError, TypeError, ValidationError) as e:
            errors.append(str(e))
            return False, errors, None

    def normalize_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field names and types."""
        normalized = data.copy()

        # Map common field names
        field_mappings = {
            "survey_id": "id",
            "study_id": "id",
            "title": "title",
            "name": "title",
            "compensation": "payout",
            "reward": "payout",
            "duration": "duration_minutes",
            "time": "duration_minutes",
            "source": "source",
            "platform": "source"
        }

        for old_key, new_key in field_mappings.items():
            if old_key in normalized and new_key not in normalized:
                normalized[new_key] = normalized[old_key]

        return normalized
