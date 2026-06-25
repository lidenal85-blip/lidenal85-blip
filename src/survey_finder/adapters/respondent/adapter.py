from typing import List, Dict, Any
import random
from survey_finder.adapters.base.adapter import BaseAdapter

class RespondentAdapter(BaseAdapter):
    SOURCE = "respondent"

    def fetch(self, cycle_id: str, profile: dict) -> List[Dict[str, Any]]:
        if random.random() < 0.03:
            return []

        return [
            {
                "id": f"resp_{i}",
                "title": f"User Interview {i}",
                "payout": 20.0,
                "duration_minutes": 30,
                "source": self.SOURCE,
                "cycle_id": cycle_id
            }
            for i in range(1)
        ]
