import random
from typing import List, Dict, Any
from survey_finder.adapters.base.adapter import BaseAdapter
from survey_finder.adapters.errors import AuthError

class CloudResearchAdapter(BaseAdapter):
    SOURCE = "cloudresearch"

    def fetch(self, cycle_id: str, profile: dict) -> List[Dict[str, Any]]:
        # simulate auth instability
        if random.random() < 0.05:
            raise AuthError("cloudresearch_session_expired")

        return [
            {
                "id": f"cloud_{i}",
                "title": f"Experiment {i}",
                "payout": 15.0,
                "duration_minutes": 12,
                "source": self.SOURCE,
                "cycle_id": cycle_id
            }
            for i in range(2)
        ]
