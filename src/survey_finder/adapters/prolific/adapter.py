import time
import random
from typing import List, Dict, Any
from survey_finder.adapters.base.adapter import BaseAdapter
from survey_finder.adapters.errors import RateLimitError

class ProlificAdapter(BaseAdapter):
    """
    Prolific ingestion adapter (mock-safe implementation).
    """

    SOURCE = "prolific"

    def fetch(self, cycle_id: str, profile: dict) -> List[Dict[str, Any]]:
        time.sleep(0.1)

        # simulate rate limit risk
        if random.random() < 0.02:
            raise RateLimitError("prolific_rate_limited")

        return [
            {
                "id": f"prolific_{i}",
                "title": f"Study {i}",
                "payout": 12.5,
                "duration_minutes": 10,
                "source": self.SOURCE,
                "cycle_id": cycle_id
            }
            for i in range(3)
        ]
