from survey_finder.runtime.circuit_breaker import CircuitBreaker
from survey_finder.runtime.schema_validator import SchemaValidator

class SafeAdapterWrapper:
    def __init__(self, adapter, validator: SchemaValidator, breaker: CircuitBreaker):
        self.adapter = adapter
        self.validator = validator
        self.breaker = breaker

    def fetch(self, cycle):
        if not self.breaker.allow():
            return []

        try:
            raw_items = self.adapter.fetch(cycle)

            validated = []
            for item in raw_items:
                if isinstance(item, dict):
                    v = self.validator.validate(item)
                    if v:
                        validated.append(v)
                else:
                    continue

            self.breaker.success()
            return validated

        except Exception:
            self.breaker.failure()
            return []
