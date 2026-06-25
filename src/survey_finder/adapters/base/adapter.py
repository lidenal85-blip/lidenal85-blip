from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseAdapter(ABC):
    """
    Contract for all source adapters.
    Must be stateless and cycle-aware.
    """

    @abstractmethod
    def fetch(self, cycle_id: str, profile: dict) -> List[Dict[str, Any]]:
        """
        Returns raw surveys from external source.
        """
        pass
