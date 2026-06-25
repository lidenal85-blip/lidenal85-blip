from survey_finder.domain.normalization.normalizer import SurveyNormalizer
from survey_finder.domain.filtering.engine import FilterEngine
from survey_finder.domain.errors import SchemaDriftError
from survey_finder.logging.logger import init_logger

logger = init_logger()

class DomainService:
    """
    Normalization + filtering pipeline.
    """

    def __init__(self):
        self.normalizer = SurveyNormalizer()
        self.filter_engine = FilterEngine()

    def process(self, raw_surveys: list, cycle_id: str):
        normalized = []
        dropped = []

        for raw in raw_surveys:
            try:
                n = self.normalizer.normalize(raw)
                normalized.append(n)
            except SchemaDriftError as e:
                logger.error(
                    "schema_drift",
                    cycle_id=cycle_id,
                    error=str(e),
                    survey_id=raw.get("id")
                )
                dropped.append(raw)

        eligible = self.filter_engine.filter(normalized)

        logger.info(
            "domain_processed",
            cycle_id=cycle_id,
            total=len(raw_surveys),
            normalized=len(normalized),
            eligible=len(eligible),
            dropped=len(dropped)
        )

        return eligible
