from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import redis
import httpx

from survey_finder.config.settings import settings
from survey_finder.logging.logger import get_logger
from survey_finder.hardening.metrics import metrics

logger = get_logger(__name__)


@dataclass
class HealthCheckResult:
    status: str  # healthy, degraded, unhealthy
    component: str
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)


class HealthChecker:
    """Extended health checker for all components."""

    def __init__(self):
        self._checks: Dict[str, callable] = {}

    def register(self, name: str, check_fn: callable) -> None:
        """Register a health check."""
        self._checks[name] = check_fn
        logger.info("health_check_registered", name=name)

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        results = {}

        for name, check_fn in self._checks.items():
            try:
                result = check_fn()
                results[name] = result
                logger.debug("health_check_ok", name=name, status=result.status)
            except Exception as e:
                results[name] = HealthCheckResult(
                    status="unhealthy",
                    component=name,
                    details={"error": str(e)}
                )
                logger.error("health_check_failed", name=name, error=str(e))

        # Update metrics
        healthy_count = sum(1 for r in results.values() if r.status == "healthy")
        metrics.gauge("health_check_healthy_count", float(healthy_count))
        metrics.gauge("health_check_total", float(len(results)))

        return results

    def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity."""
        try:
            client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            return HealthCheckResult(
                status="healthy",
                component="redis",
                details={"url": settings.REDIS_URL}
            )
        except Exception as e:
            return HealthCheckResult(
                status="unhealthy",
                component="redis",
                details={"error": str(e)}
            )

    def check_postgres(self) -> HealthCheckResult:
        """Check PostgreSQL connectivity."""
        try:
            # Try to connect via DSN
            import psycopg2
            conn = psycopg2.connect(settings.POSTGRES_DSN)
            conn.close()
            return HealthCheckResult(
                status="healthy",
                component="postgres",
                details={"dsn": settings.POSTGRES_DSN.split("@")[1] if "@" in settings.POSTGRES_DSN else "unknown"}
            )
        except ImportError:
            return HealthCheckResult(
                status="degraded",
                component="postgres",
                details={"error": "psycopg2 not installed"}
            )
        except Exception as e:
            return HealthCheckResult(
                status="unhealthy",
                component="postgres",
                details={"error": str(e)}
            )

    def check_telegram(self) -> HealthCheckResult:
        """Check Telegram API connectivity."""
        try:
            # Try to get bot info (requires token)
            bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
            if not bot_token:
                return HealthCheckResult(
                    status="degraded",
                    component="telegram",
                    details={"error": "TELEGRAM_BOT_TOKEN not configured"}
                )

            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
                if response.status_code == 200:
                    return HealthCheckResult(
                        status="healthy",
                        component="telegram",
                        details={"bot_username": response.json().get("result", {}).get("username")}
                    )
                else:
                    return HealthCheckResult(
                        status="unhealthy",
                        component="telegram",
                        details={"status_code": response.status_code}
                    )
        except Exception as e:
            return HealthCheckResult(
                status="unhealthy",
                component="telegram",
                details={"error": str(e)}
            )
