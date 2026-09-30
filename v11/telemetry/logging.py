"""Structured JSON logging for RD Guard V11.

Every log record is emitted as a single JSON object with a stable set of
fields (timestamp, level, logger name, message, and optional exception
info), making logs easy to ship to and query in a log aggregator.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional


class JsonFormatter(logging.Formatter):
    """A ``logging.Formatter`` that renders records as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def get_logger(
    name: str = "rd_guard",
    level: Optional[str] = None,
    stream=None,
) -> logging.Logger:
    """Return a logger configured to emit structured JSON log lines.

    Calling this repeatedly with the same ``name`` reuses the existing
    logger and does not attach duplicate handlers.
    """
    logger = logging.getLogger(name)
    if not any(isinstance(h.formatter, JsonFormatter) for h in logger.handlers):
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel((level or "INFO").upper())
    logger.propagate = False
    return logger
