from typing import Dict, Any
from survey_finder.contracts.survey import Survey


class MessageTemplates:
    """Message templates for notifications."""

    @staticmethod
    def survey_eligible(survey: Survey, score: float, reasons: list[str]) -> str:
        """Template for eligible survey notification."""
        return (
            f"📋 *New Survey Available*\n\n"
            f"*Title:* {survey.title}\n"
            f"*Platform:* {survey.source}\n"
            f"*Payout:* ${survey.payout:.2f}\n"
            f"*Duration:* {survey.duration_minutes} min\n"
            f"*Hourly Rate:* ${(survey.payout / max(1, survey.duration_minutes)) * 60:.2f}/hr\n"
            f"*Match Score:* {score:.0%}\n"
            f"*Reasons:* {', '.join(reasons[:3])}\n"
            f"\n🔗 [View Survey](#)"
        )

    @staticmethod
    def survey_review(survey: Survey, score: float, reasons: list[str]) -> str:
        """Template for review required notification."""
        return (
            f"⚠️ *Survey Needs Review*\n\n"
            f"*Title:* {survey.title}\n"
            f"*Platform:* {survey.source}\n"
            f"*Payout:* ${survey.payout:.2f}\n"
            f"*Match Score:* {score:.0%}\n"
            f"*Issues:* {', '.join(reasons[:3])}\n"
        )

    @staticmethod
    def delivery_failed(error: str, retry_count: int) -> str:
        """Template for delivery failure notification."""
        return (
            f"❌ *Delivery Failed*\n\n"
            f"*Error:* {error}\n"
            f"*Retry Attempts:* {retry_count}\n"
            f"*Please check DLQ for details*"
        )
