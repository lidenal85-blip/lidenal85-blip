from typing import Dict, Any, List
from survey_finder.domain.normalization.models import NormalizedSurvey
from survey_finder.domain.errors import SchemaDriftError

class SurveyNormalizer:
    """
    Converts raw adapter payloads into canonical domain model.
    """

    REQUIRED_FIELDS = {"id", "title", "payout", "duration_minutes", "source", "cycle_id"}

    def normalize(self, raw: Dict[str, Any]) -> NormalizedSurvey:
        missing = self.REQUIRED_FIELDS - set(raw.keys())

        if missing:
            raise SchemaDriftError(f"missing_fields={missing}")

        try:
            return NormalizedSurvey(**raw)
        except Exception as e:
            raise SchemaDriftError(str(e))


    def normalize_batch(self, raw_list: List[Dict[str, Any]]) -> List[NormalizedSurvey]:
        result = []
        for item in raw_list:
            result.append(self.normalize(item))
        return result
