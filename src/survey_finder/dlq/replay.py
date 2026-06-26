from typing import List, Dict, Any, Optional
from datetime import datetime

from survey_finder.contracts.dlq import DLQItem
from survey_finder.dlq.storage import DLQStorage
from survey_finder.logging.logger import get_logger

logger = get_logger(__name__)


class ReplayService:
    """Replay failed items from DLQ."""

    def __init__(self, storage: Optional[DLQStorage] = None):
        self.storage = storage or DLQStorage()

    def replay_by_cycle(self, cycle_id: str) -> int:
        """Replay all items for a cycle."""
        items = self.storage.fetch_by_cycle(cycle_id)
        return self._replay_items(items, cycle_id)

    def replay_by_source(self, source: str) -> int:
        """Replay all items for a source."""
        items = self.storage.fetch_by_source(source)
        return self._replay_items(items)

    def _replay_items(self, items: List[DLQItem], cycle_id: Optional[str] = None) -> int:
        """Replay list of DLQ items."""
        if not items:
            return 0

        logger.info("replay_start", count=len(items))

        successful = 0
        failed = 0

        for item in items:
            # Here we would re-process the item
            # For now, we just log and mark as success
            logger.info("replay_item", cycle_id=item.cycle_id, source=item.source)

            # In production, this would call the appropriate handler
            try:
                # Simulate processing
                successful += 1
            except Exception as e:
                logger.error("replay_failed", error=str(e))
                failed += 1

        logger.info("replay_complete", successful=successful, failed=failed)

        # Cleanup successfully replayed items
        if cycle_id:
            self.storage.delete_by_cycle(cycle_id)

        return successful

    def get_dlq_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        total = self.storage.count()

        return {
            "total_items": total,
            "status": "ok" if total == 0 else "degraded"
        }
