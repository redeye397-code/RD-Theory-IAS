"""Environment-driven runtime configuration for RD Guard V11.

Configuration is deliberately simple: every setting is read from an
environment variable with a safe default, so the application can be
deployed across ``dev``/``staging``/``prod`` environments without any code
changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

VALID_ENVIRONMENTS = ("dev", "staging", "prod")

DEFAULT_ENV = "dev"
DEFAULT_METRICS_PORT = 9090
DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class Config:
    """Resolved runtime configuration.

    Attributes:
        env: Deployment environment (``dev``, ``staging``, or ``prod``).
        metrics_port: TCP port for the Prometheus metrics exporter.
        webhook_url: Optional webhook URL used for alerting. ``None`` when
            no webhook is configured, in which case alerting is skipped.
        log_level: Logging level name (e.g. ``"INFO"``, ``"DEBUG"``).
    """

    env: str = DEFAULT_ENV
    metrics_port: int = DEFAULT_METRICS_PORT
    webhook_url: Optional[str] = None
    log_level: str = DEFAULT_LOG_LEVEL


def load_config(environ: Optional[dict] = None) -> Config:
    """Load ``Config`` from environment variables.

    Args:
        environ: Optional mapping to read from instead of ``os.environ``
            (primarily useful for tests).

    Recognized variables:
        ``RD_GUARD_ENV`` -- deployment environment, defaults to ``"dev"``.
        ``METRICS_PORT`` -- metrics exporter port, defaults to ``9090``.
        ``RD_GUARD_WEBHOOK_URL`` -- webhook alert target, defaults to unset.
        ``RD_GUARD_LOG_LEVEL`` -- logging level, defaults to ``"INFO"``.

    Malformed values fall back to safe defaults rather than raising, so a
    bad deployment environment never prevents the guard from starting.
    """
    env_source = os.environ if environ is None else environ

    env = env_source.get("RD_GUARD_ENV", DEFAULT_ENV) or DEFAULT_ENV
    if env not in VALID_ENVIRONMENTS:
        env = DEFAULT_ENV

    raw_port = env_source.get("METRICS_PORT", str(DEFAULT_METRICS_PORT))
    try:
        metrics_port = int(raw_port)
    except (TypeError, ValueError):
        metrics_port = DEFAULT_METRICS_PORT

    webhook_url = env_source.get("RD_GUARD_WEBHOOK_URL") or None

    log_level = env_source.get("RD_GUARD_LOG_LEVEL", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL
    log_level = log_level.upper()

    return Config(
        env=env,
        metrics_port=metrics_port,
        webhook_url=webhook_url,
        log_level=log_level,
    )
