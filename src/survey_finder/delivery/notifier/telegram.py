import time
import random
from survey_finder.delivery.errors import RateLimitError

class TelegramNotifier:
    """
    External delivery boundary (Telegram API abstraction).
    """

    def __init__(self, token: str = "mock-token"):
        self.token = token

    def send_message(self, chat_id: str, text: str, idempotency_key: str) -> bool:
        time.sleep(0.05)

        # simulate rate limit risk
        if random.random() < 0.03:
            raise RateLimitError("telegram_rate_limited")

        # simulate occasional failure
        if random.random() < 0.01:
            return False

        return True
