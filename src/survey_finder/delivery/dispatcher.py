import httpx
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from survey_finder.config.settings import settings
from survey_finder.idempotency.gate import RedisIdempotencyGate
from survey_finder.buffer.queue import RedisBuffer
from survey_finder.delivery.retry import RetryPolicy, RetryExecutor
from survey_finder.delivery.templates import MessageTemplates
from survey_finder.logging.logger import init_logger
from survey_finder.contracts.dlq import DLQItem

logger = init_logger()


class TelegramDispatcher:
    """Dispatches notifications via Telegram."""

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        buffer: Optional[RedisBuffer] = None,
        idempotency_gate: Optional[RedisIdempotencyGate] = None
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.buffer = buffer
        self.idempotency_gate = idempotency_gate or RedisIdempotencyGate()
        self.retry_policy = RetryPolicy()
        self.retry_executor = RetryExecutor(self.retry_policy)
        self.templates = MessageTemplates()

    async def dispatch(self, survey: Dict[str, Any], score: float, reasons: list[str]) -> Dict[str, Any]:
        """Dispatch survey notification via Telegram."""
        from survey_finder.contracts.survey import Survey
        survey_obj = Survey(**survey)

        # Build message
        if score >= 0.7:
            message = self.templates.survey_eligible(survey_obj, score, reasons)
        else:
            message = self.templates.survey_review(survey_obj, score, reasons)

        # Create idempotency key
        idempotency_key = f"telegram:{survey_obj.id}:{hash(message)}"

        # Check idempotency
        result = self.idempotency_gate.check_and_set(idempotency_key)
        if result.status == "DUPLICATE":
            logger.info("duplicate_message_skipped", survey_id=survey_obj.id)
            return {"status": "DUPLICATE", "message_id": None}

        # Send via Telegram with retry
        try:
            response = await self.retry_executor.execute(
                self._send_telegram,
                message
            )

            logger.info("telegram_sent", survey_id=survey_obj.id)
            return {"status": "DELIVERED", "message_id": response.get("result", {}).get("message_id")}

        except Exception as e:
            logger.error("telegram_failed", survey_id=survey_obj.id, error=str(e))

            # Push to DLQ
            if self.buffer:
                self._push_to_dlq(survey_obj, str(e))

            return {"status": "FAILED", "error": str(e)}

    async def _send_telegram(self, message: str) -> Dict[str, Any]:
        """Send message via Telegram API."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                }
            )

            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("description", f"HTTP {response.status_code}")
                raise RuntimeError(f"Telegram API error: {error_msg}")

            return response.json()

    def _push_to_dlq(self, survey, reason: str) -> None:
        """Push failed survey to DLQ."""
        if not self.buffer:
            return

        dlq_item = DLQItem(
            cycle_id="unknown",
            source=survey.source,
            payload_type="survey",
            raw_payload=survey.model_dump(),
            reason=f"delivery_failed: {reason}",
            failed_at=datetime.utcnow()
        )

        self.buffer.push({
            "type": "dlq",
            "data": dlq_item.model_dump()
        })
        logger.info("dlq_pushed", survey_id=survey.id, reason=reason)


class NotificationDispatcher:
    """Alias for TelegramDispatcher."""

    def __init__(self, bot_token: str, chat_id: str, buffer: Optional[RedisBuffer] = None):
        self.dispatcher = TelegramDispatcher(bot_token, chat_id, buffer)

    async def dispatch(self, survey: Dict[str, Any], score: float, reasons: list[str]) -> Dict[str, Any]:
        return await self.dispatcher.dispatch(survey, score, reasons)
