"""
survey_finder.logging.logger
============================
Централизованная система логирования.

Архитектура:
  - structlog JSON → stdout (для prod / docker / journald)
  - Session log → /opt/leviathan_engine/logs/sessions/YYYY-MM-DD.md (append)
    Пишем только ключевые события (INFO+), не debug-шум.

Использование:
    from survey_finder.logging.logger import get_logger
    logger = get_logger(__name__)
    logger.info("event_name", key=value)

Обратная совместимость:
    init_logger() оставлен как алиас для плавной миграции.
"""
from __future__ import annotations

import logging
import datetime
from pathlib import Path
from typing import Any

import structlog

# ── Конфигурация ──────────────────────────────────────────────────────────────

SESSION_LOG_DIR = Path("/opt/leviathan_engine/logs/sessions")
_CONFIGURED = False


def _ensure_configured() -> None:
    """Инициализирует structlog один раз (идемпотентно)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    try:
        SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    _CONFIGURED = True


# ── Session log (append) ───────────────────────────────────────────────────────

def _session_log(event: str, level: str = "INFO", **kw: Any) -> None:
    """
    Дописывает строку в дневной MD-лог сессии.
    Вызывается автоматически из SessionLogger для INFO+.
    Никогда не кидает исключений.
    """
    try:
        today = datetime.date.today().isoformat()
        ts    = datetime.datetime.now().strftime("%H:%M:%S")
        icon  = {"INFO": "✓", "WARNING": "⚠", "ERROR": "✗"}.get(level, "·")
        extra = " | ".join(f"{k}={v}" for k, v in kw.items()) if kw else ""
        line  = f"[{ts}] {icon} {event}" + (f" | {extra}" if extra else "") + "\n"

        log_file = SESSION_LOG_DIR / f"{today}.md"
        if not log_file.exists():
            log_file.write_text(
                f"# Session {today} — survey-finder\n\n", encoding="utf-8"
            )
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass  # лог не должен ломать основную логику


# ── Обёртка логгера ───────────────────────────────────────────────────────────

class _SessionLogger:
    """
    Тонкая обёртка над structlog.BoundLogger.
    Для уровней INFO / WARNING / ERROR дополнительно пишет в session-лог.
    Поддерживает тот же вызов: logger.info("event", key=value)
    """

    def __init__(self, name: str) -> None:
        _ensure_configured()
        self._log = structlog.get_logger(name)
        self._name = name

    def debug(self, event: str, **kw: Any) -> None:
        self._log.debug(event, **kw)

    def info(self, event: str, **kw: Any) -> None:
        self._log.info(event, **kw)
        _session_log(event, "INFO", **kw)

    def warning(self, event: str, **kw: Any) -> None:
        self._log.warning(event, **kw)
        _session_log(event, "WARNING", **kw)

    def error(self, event: str, **kw: Any) -> None:
        self._log.error(event, **kw)
        _session_log(event, "ERROR", **kw)

    # structlog иногда зовёт bind / unbind
    def bind(self, **kw: Any) -> "_SessionLogger":
        bound = _SessionLogger.__new__(_SessionLogger)
        bound._log  = self._log.bind(**kw)
        bound._name = self._name
        return bound


# ── Публичный API ──────────────────────────────────────────────────────────────

def get_logger(name: str = "survey_finder") -> _SessionLogger:
    """Возвращает логгер с поддержкой session-лога. Рекомендуемый способ."""
    return _SessionLogger(name)


def init_logger() -> _SessionLogger:
    """Обратная совместимость с существующими вызовами init_logger()."""
    return get_logger("survey_finder")