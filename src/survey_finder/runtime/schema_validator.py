from survey_finder.runtime.dlq import DeadLetterQueue

class SchemaValidator:
    def __init__(self, dlq: DeadLetterQueue):
        self.dlq = dlq

    def validate(self, raw: dict) -> dict | None:
        required = {"source", "schema_version", "payload"}

        if not isinstance(raw, dict):
            self.dlq.push({"error": "not_dict", "raw": str(raw)})
            return None

        if not required.issubset(set(raw.keys())):
            self.dlq.push({"error": "missing_fields", "raw": raw})
            return None

        if not isinstance(raw["payload"], dict):
            self.dlq.push({"error": "invalid_payload", "raw": raw})
            return None

        return raw
