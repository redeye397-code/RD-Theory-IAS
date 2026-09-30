"""Tests for the V11 webhook alerting integration."""

from v11.integrations.webhook import send_webhook_alert


class _FakeResponse:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _fake_opener(status=200):
    def opener(request, timeout=None):
        return _FakeResponse(status)

    return opener


def _raising_opener(exc):
    def opener(request, timeout=None):
        raise exc

    return opener


def test_send_webhook_alert_returns_false_when_url_missing():
    assert send_webhook_alert(None, {"message": "unsafe state"}) is False
    assert send_webhook_alert("", {"message": "unsafe state"}) is False


def test_send_webhook_alert_returns_true_on_success():
    result = send_webhook_alert(
        "https://hooks.example.com/alert",
        {"message": "unsafe state"},
        opener=_fake_opener(status=200),
    )

    assert result is True


def test_send_webhook_alert_returns_false_on_error_status():
    result = send_webhook_alert(
        "https://hooks.example.com/alert",
        {"message": "unsafe state"},
        opener=_fake_opener(status=500),
    )

    assert result is False


def test_send_webhook_alert_fails_safely_on_network_error():
    import urllib.error

    result = send_webhook_alert(
        "https://hooks.example.com/alert",
        {"message": "unsafe state"},
        opener=_raising_opener(urllib.error.URLError("boom")),
    )

    assert result is False


def test_send_webhook_alert_fails_safely_on_timeout():
    result = send_webhook_alert(
        "https://hooks.example.com/alert",
        {"message": "unsafe state"},
        opener=_raising_opener(TimeoutError("timed out")),
    )

    assert result is False


def test_send_webhook_alert_fails_safely_on_unserializable_payload():
    result = send_webhook_alert(
        "https://hooks.example.com/alert",
        {"bad": object()},
    )

    assert result is False
