"""Tests for the V11 structured JSON logging helper."""

import io
import json
import logging

from v11.telemetry.logging import JsonFormatter, get_logger


def _make_logger(name):
    stream = io.StringIO()
    logger = get_logger(name, stream=stream)
    return logger, stream


def test_get_logger_emits_json_with_expected_fields():
    logger, stream = _make_logger("test_v11_logging_basic")

    logger.info("guard started")

    record = json.loads(stream.getvalue().strip())
    assert record["level"] == "INFO"
    assert record["logger"] == "test_v11_logging_basic"
    assert record["message"] == "guard started"
    assert "timestamp" in record and record["timestamp"]


def test_get_logger_includes_exception_info():
    logger, stream = _make_logger("test_v11_logging_exception")

    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("something failed")

    record = json.loads(stream.getvalue().strip())
    assert record["level"] == "ERROR"
    assert "exception" in record
    assert "ValueError" in record["exception"]


def test_get_logger_respects_configured_level():
    logger, stream = _make_logger("test_v11_logging_level")
    logger.setLevel("INFO")

    logger.debug("should not appear")
    logger.info("should appear")

    output = stream.getvalue().strip().splitlines()
    assert len(output) == 1
    assert json.loads(output[0])["message"] == "should appear"


def test_get_logger_does_not_attach_duplicate_handlers():
    stream = io.StringIO()
    logger_a = get_logger("test_v11_logging_reuse", stream=stream)
    logger_b = get_logger("test_v11_logging_reuse", stream=stream)

    assert logger_a is logger_b
    json_handlers = [
        h for h in logger_a.handlers if isinstance(h.formatter, JsonFormatter)
    ]
    assert len(json_handlers) == 1


def test_json_formatter_produces_valid_json_for_bare_record():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="rd_guard",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="disk usage high",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))
    assert payload["level"] == "WARNING"
    assert payload["logger"] == "rd_guard"
    assert payload["message"] == "disk usage high"
    assert "timestamp" in payload
    assert "exception" not in payload
