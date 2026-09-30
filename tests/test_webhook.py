from urllib.error import URLError

import pytest

from rd_webhook import WebhookAlerter


class FakeResponse:
    def __init__(self, status=204):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_sends_json_alert():
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return FakeResponse()

    alerter = WebhookAlerter(opener=opener)

    assert alerter.send("https://example.test/hook", {"event": "blocked"}) is True
    assert len(requests) == 1
    assert requests[0][0].get_method() == "POST"
    assert requests[0][0].get_header("Content-type") == "application/json"
    assert requests[0][1] == 5


def test_unsuccessful_http_status_returns_false():
    alerter = WebhookAlerter(opener=lambda request, timeout: FakeResponse(503))

    assert alerter.send("https://example.test/hook", {"event": "blocked"}) is False


def test_cooldown_suppresses_repeated_alerts():
    now = [10.0]
    requests = []
    alerter = WebhookAlerter(
        cooldown_seconds=30,
        opener=lambda request, timeout: requests.append(request) or FakeResponse(),
        clock=lambda: now[0],
    )

    assert alerter.send("https://example.test/hook", {"event": "blocked"}) is True
    assert alerter.send("https://example.test/hook", {"event": "blocked"}) is False
    assert len(requests) == 1

    now[0] = 40.0
    assert alerter.send("https://example.test/hook", {"event": "blocked"}) is True
    assert len(requests) == 2


def test_failed_request_is_suppressed_during_cooldown():
    now = [0.0]
    attempts = []

    def fail_request(request, timeout):
        attempts.append(request)
        raise URLError("unavailable")

    alerter = WebhookAlerter(
        cooldown_seconds=30, opener=fail_request, clock=lambda: now[0]
    )

    assert alerter.send("https://example.test/hook", {"event": "blocked"}) is False
    assert alerter.send("https://example.test/hook", {"event": "blocked"}) is False
    assert len(attempts) == 1


@pytest.mark.parametrize(
    ("webhook_url", "payload"),
    [
        (None, {"event": "blocked"}),
        ("", {"event": "blocked"}),
        ("file:///tmp/webhook", {"event": "blocked"}),
        ("https://[invalid", {"event": "blocked"}),
        ("https://example.test/hook", []),
        ("https://example.test/hook", {"value": object()}),
        ("https://example.test/hook", {"value": float("nan")}),
    ],
)
def test_invalid_url_or_payload_fails_without_request(webhook_url, payload):
    requests = []
    alerter = WebhookAlerter(
        opener=lambda request, timeout: requests.append(request) or FakeResponse()
    )

    assert alerter.send(webhook_url, payload) is False
    assert requests == []


@pytest.mark.parametrize(
    "cooldown", [-1, float("inf"), float("nan"), True, "1", 10**1000]
)
def test_invalid_cooldown_is_rejected(cooldown):
    with pytest.raises(ValueError):
        WebhookAlerter(cooldown_seconds=cooldown)
