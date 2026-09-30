"""Fail-safe, rate-limited webhook notifications for RD Guard."""

import json
import math
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class WebhookAlerter:
    """Send webhook alerts with a per-instance cooldown.

    Failed requests also start the cooldown, preventing repeated failures from
    creating an alert storm. Notification failures never raise to the caller.
    """

    def __init__(self, cooldown_seconds=60.0, opener=None, clock=None):
        if (
            not isinstance(cooldown_seconds, (int, float))
            or isinstance(cooldown_seconds, bool)
        ):
            raise ValueError("cooldown_seconds must be a finite non-negative number")
        try:
            cooldown_seconds = float(cooldown_seconds)
        except OverflowError as exc:
            raise ValueError(
                "cooldown_seconds must be a finite non-negative number"
            ) from exc
        if not math.isfinite(cooldown_seconds) or cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be a finite non-negative number")
        self.cooldown_seconds = cooldown_seconds
        self._opener = opener if opener is not None else urlopen
        self._clock = clock if clock is not None else time.monotonic
        self._lock = threading.Lock()
        self._last_attempt = None

    def send(self, webhook_url, payload):
        """Send a JSON object, returning False for invalid, suppressed, or failed alerts."""
        if not isinstance(webhook_url, str):
            return False
        try:
            parsed_url = urlparse(webhook_url)
        except ValueError:
            return False
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            return False
        if not isinstance(payload, dict):
            return False

        try:
            body = json.dumps(payload, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError, OverflowError, RecursionError):
            return False

        with self._lock:
            now = self._clock()
            if (
                self._last_attempt is not None
                and now - self._last_attempt < self.cooldown_seconds
            ):
                return False
            self._last_attempt = now

        try:
            request = Request(
                webhook_url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self._opener(request, timeout=5) as response:
                status = getattr(response, "status", None)
                return isinstance(status, int) and 200 <= status < 300
        except (HTTPError, URLError, OSError, TimeoutError, ValueError, TypeError):
            return False


__all__ = ["WebhookAlerter"]
