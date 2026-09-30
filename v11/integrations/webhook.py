"""Minimal webhook integration for unsafe-state alerting.

This is RD Guard's one real external integration: when an unsafe/compromised
state is detected, ``send_webhook_alert`` posts a JSON payload to a
configured webhook URL (e.g. Slack or Discord's incoming-webhook endpoints).

The integration is intentionally fail-safe: a missing URL, network error,
timeout, or non-2xx response is swallowed and reported as ``False`` rather
than raised, so alerting failures never crash or block the guard itself.
"""

from __future__ import annotations

import json
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_SECONDS = 5


def send_webhook_alert(
    webhook_url: Optional[str],
    payload: dict,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: Any = None,
) -> bool:
    """Send ``payload`` as JSON to ``webhook_url``.

    Args:
        webhook_url: The webhook endpoint to POST to. If falsy, no request
            is made and ``False`` is returned.
        payload: A JSON-serializable dict describing the alert.
        timeout: Request timeout in seconds.
        opener: Optional callable used instead of ``urllib.request.urlopen``
            (primarily for tests).

    Returns:
        ``True`` if the webhook accepted the alert (HTTP 2xx), ``False``
        otherwise -- including when no URL is configured, the request
        fails, or the server returns an error status.
    """
    if not webhook_url:
        return False

    try:
        body = json.dumps(payload).encode("utf-8")
    except (TypeError, ValueError):
        return False

    request = Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    send = opener if opener is not None else urlopen

    try:
        with send(request, timeout=timeout) as response:
            status = getattr(response, "status", None)
            if status is None:
                status = getattr(response, "code", 200)
            return 200 <= status < 300
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return False
