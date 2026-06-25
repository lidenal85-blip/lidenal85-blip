from pydantic import BaseModel
from typing import Any, Dict

class RawPayload(BaseModel):
    source: str
    schema_version: str
    payload: Dict[str, Any]
