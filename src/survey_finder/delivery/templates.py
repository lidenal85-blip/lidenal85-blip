from typing import Dict, Any
from survey_finder.contracts.survey import Survey


class MessageTemplates:
    """Telegram message templates."""

    @staticmethod
    def survey_eligible(survey: Survey, score: float, reasons: list[str]) -> str:
        rate_str = f"${survey.hourly_rate:.2f}/hr" if survey.hourly_rate > 0 else "N/A"
        places = f"\n*Places:* {survey.places_available}" if survey.places_available else ""
        deadline = f"\n*Deadline:* {survey.deadline}" if survey.deadline else ""
        url_line = f"\n\n🔗 [Open Survey]({survey.url})" if survey.url else ""

        passed = [r for r in reasons if not r.startswith("FAIL")]
        return (
            f"📋 *New Survey — {survey.source.title()}*\n\n"
            f"*{survey.title}*\n"
            f"*Payout:* ${survey.payout:.2f} \u00b7 {survey.duration_minutes} min \u00b7 {rate_str}\n"
            f"*Score:* {score:.0%}"
            f"{places}{deadline}{url_line}\n"
            f"\n✅ {' \u00b7 '.join(passed[:3])}"
        )

    @staticmethod
    def survey_review(survey: Survey, score: float, reasons: list[str]) -> str:
        url_line = f"\n\n🔗 [Open Survey]({survey.url})" if survey.url else ""
        fails = [r.replace("FAIL:", "") for r in reasons if r.startswith("FAIL")]
        return (
            f"⚠️ *Review Required — {survey.source.title()}*\n\n"
            f"*{survey.title}*\n"
            f"*Payout:* ${survey.payout:.2f} \u00b7 {survey.duration_minutes} min\n"
            f"*Score:* {score:.0%}"
            f"{url_line}\n"
            f"\n⚠️ Issues: {', '.join(fails[:3])}"
        )

    @staticmethod
    def delivery_failed(error: str, retry_count: int) -> str:
        return (
            f"❌ *Delivery Failed*\n\n"
            f"*Error:* {error}\n"
            f"*Retries:* {retry_count}\n"
            f"Check DLQ for details."
        )