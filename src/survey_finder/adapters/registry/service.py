from typing import List, Dict, Any
from survey_finder.adapters.registry.registry import AdapterRegistry
from survey_finder.adapters.errors import AdapterError
from survey_finder.logging.logger import init_logger

logger = init_logger()

class AdapterService:
    """
    Runs all adapters safely per cycle.
    Fail-isolated execution.
    """

    def __init__(self):
        self.registry = AdapterRegistry()

    def fetch_all(self, cycle_id: str, profile: dict) -> List[Dict[str, Any]]:
        results = []

        for adapter in self.registry.all():
            try:
                data = adapter.fetch(cycle_id, profile)
                results.extend(data)

            except AdapterError as e:
                logger.error(
                    "adapter_error",
                    adapter=adapter.__class__.__name__,
                    cycle_id=cycle_id,
                    error=str(e)
                )
                continue

            except Exception as e:
                logger.error(
                    "adapter_unknown_error",
                    adapter=adapter.__class__.__name__,
                    cycle_id=cycle_id,
                    error=str(e)
                )
                continue

        return results
