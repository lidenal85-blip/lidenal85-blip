import time
from survey_finder.delivery.notifier.telegram import TelegramNotifier
from survey_finder.delivery.dispatcher.idempotency import DeliveryIdempotencyStore
from survey_finder.delivery.errors import RateLimitError
from survey_finder.logging.logger import init_logger

logger = init_logger()

class NotificationDispatcher:
    """
    Safe delivery pipeline:
    - idempotency protection
    - retry on rate limit
    - backpressure-aware behavior
    """

    def __init__(self, token: str = "mock-token"):
        self.notifier = TelegramNotifier(token)
        self.store = DeliveryIdempotencyStore()

    def dispatch(self, chat_id: str, survey: dict, cycle_id: str) -> bool:
        key = f"{survey['id']}:{chat_id}"

        if not self.store.mark_sent(key):
            logger.info("duplicate_skipped", cycle_id=cycle_id, survey_id=survey["id"])
            return False

        text = f"{survey['title']} | ${survey['payout']} | {survey['source']}"

        retries = 3

        for attempt in range(retries):
            try:
                ok = self.notifier.send_message(chat_id, text, key)

                if ok:
                    logger.info("delivery_success", cycle_id=cycle_id, survey_id=survey["id"])
                    return True

            except RateLimitError:
                wait = 2 ** attempt
                logger.warning("telegram_rate_limit", retry_in=wait, cycle_id=cycle_id)
                time.sleep(wait)

        logger.error("delivery_failed", cycle_id=cycle_id, survey_id=survey["id"])
        return False
