from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class FilterEngine:
    """
    Minimal contract-compliant filter engine.
    Expected by A2.x tests.
    """

    def apply(self, items: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Deterministic filter:
        - removes items below min_hourly_rate
        - ensures stable output order
        """

        min_rate = user_profile.get("min_hourly_rate", 0)

        filtered = [
            item for item in items
            if float(item.get("payout", 0)) >= min_rate
        ]

        # deterministic ordering
        filtered.sort(key=lambda x: float(x.get("payout", 0)), reverse=True)

        return filtered
