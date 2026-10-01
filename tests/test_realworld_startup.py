"""Tests for the V11.2.0 real-world startup path (``realworld.py``).

These guard against the package-layout regression where ``rd_guard`` was a
flat module and the V11 submodules it documents/imports --
``rd_guard.v11.config`` and ``rd_guard.v11.telemetry.logging`` -- did not
exist, causing ``realworld.py`` to fail immediately on import.
"""

import importlib

import pytest

from rd_guard import RDGuard
from rd_guard.v11.config import GuardConfig
from rd_guard.v11.telemetry.logging import get_logger


def test_guard_config_has_expected_defaults_and_env():
    config = GuardConfig(env="prod")

    assert config.env == "prod"
    assert config.bloat_threshold == 0.7
    assert config.drift_threshold == 0.6
    assert config.stall_threshold == 0.6


def test_get_logger_is_idempotent_and_usable():
    logger = get_logger("rd_guard.tests.realworld")
    same_logger = get_logger("rd_guard.tests.realworld")

    assert logger is same_logger
    assert len(logger.handlers) == 1
    logger.info("startup check")


def test_rdguard_accepts_v11_config_and_evaluate_alias():
    guard = RDGuard(config=GuardConfig(env="prod"))

    allowed = guard.evaluate({"action": "read_file"})
    assert allowed.state == "ALLOW"
    assert allowed.blocked is False

    blocked = guard.evaluate({"deleting_tests": True})
    assert blocked.state == "BLOCK"
    assert blocked.blocked is True


def test_realworld_entrypoint_imports_and_serves_requests():
    fastapi_testclient = pytest.importorskip("fastapi.testclient")

    realworld = importlib.import_module("realworld")

    client = fastapi_testclient.TestClient(realworld.app)

    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["status"] == "V11.2.0 LIVE"

    allowed = client.post("/check", json={"data": {"action": "read_file"}})
    assert allowed.status_code == 200
    assert allowed.json()["state"] == "ALLOW"
    assert allowed.json()["blocked"] is False

    blocked = client.post("/check", json={"data": {"deleting_tests": True}})
    assert blocked.status_code == 200
    assert blocked.json()["state"] == "BLOCK"
    assert blocked.json()["blocked"] is True


def test_realworld_reports_actionable_error_when_v11_layout_missing(monkeypatch):
    pytest.importorskip("fastapi")
    import sys

    monkeypatch.setitem(sys.modules, "rd_guard.v11.config", None)
    monkeypatch.delitem(sys.modules, "realworld", raising=False)

    with pytest.raises(ImportError) as exc_info:
        importlib.import_module("realworld")

    message = str(exc_info.value)
    assert "pip install -e ." in message
    assert "rd_guard/v11/config.py" in message

    # Clean up so later tests re-import a fresh, working realworld module.
    monkeypatch.delitem(sys.modules, "realworld", raising=False)
