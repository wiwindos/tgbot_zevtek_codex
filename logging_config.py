from __future__ import annotations

import logging
import os
from typing import Any

import structlog


def configure_logging(level: str | None = None) -> None:
    """Configure structured JSON logging for the application."""
    logging_level = level or os.getenv("LOG_LEVEL", "INFO")
    level_num = getattr(logging, str(logging_level), logging.INFO)

    def rename_exc(_: Any, __: str, event: dict[str, Any]) -> dict[str, Any]:
        if "exception" in event:
            event["exc_info"] = event.pop("exception")
        return event

    processors: list[Any] = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        rename_exc,
        structlog.processors.JSONRenderer(),
    ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logging.basicConfig(level=level_num)

    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        import sentry_sdk

        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1)
