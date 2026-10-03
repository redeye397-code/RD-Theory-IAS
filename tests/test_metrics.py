import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from _rd_metrics import PrometheusMetrics
from _rd_metrics_server import start_metrics_server, stop_metrics_server
from _rd_state_machine import RecoveryError, SafetyStateMachine, seal_checkpoint
from _rd_vault_core import GhostVaultProduction
from rd_guard import RDGuard
from rd_executor import GuardedExecutor


def test_metrics_noop_fallback_is_safe():
    metrics = PrometheusMetrics(prometheus_client=None)

    metrics.record_decision("ALLOW")
    metrics.record_transition("NORMAL", "STABILIZING", "STABILIZE")
    metrics.set_state("NORMAL")
    metrics.record_vault_operation("checkpoint_seal", "success")
    with metrics.time("guard_observe_seconds"):
        pass

    assert metrics.enabled is False
    assert metrics.render() == b""


def test_default_metrics_falls_back_when_prometheus_client_is_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "prometheus_client", None)
    assert PrometheusMetrics().enabled is False


def test_metrics_http_server_exposes_metrics_path():
    metrics = PrometheusMetrics(prometheus_client=None)
    server = start_metrics_server("127.0.0.1", 0, metrics)
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/metrics") as response:
            assert response.status == 200
            assert response.read() == b""
        with pytest.raises(HTTPError):
            urlopen(f"http://127.0.0.1:{server.server_port}/")
    finally:
        stop_metrics_server("127.0.0.1", 0)


def test_metrics_http_server_reuses_same_listener():
    metrics = PrometheusMetrics(prometheus_client=None)
    first_server = start_metrics_server("127.0.0.1", 0, metrics)
    try:
        assert start_metrics_server("127.0.0.1", 0, metrics) is first_server
    finally:
        stop_metrics_server("127.0.0.1", 0)


def test_metrics_http_server_closes_stale_listener_before_replacing():
    import socket

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    metrics_a = PrometheusMetrics(prometheus_client=None)
    metrics_b = PrometheusMetrics(prometheus_client=None)
    first_server = start_metrics_server("127.0.0.1", port, metrics_a)
    try:
        # Requesting a different ``metrics`` object for the same address should
        # replace (not leak) the existing listener, freeing the port so the
        # new server can bind without raising "Address already in use".
        second_server = start_metrics_server("127.0.0.1", port, metrics_b)
        assert second_server is not first_server
        assert first_server.fileno() == -1
    finally:
        stop_metrics_server("127.0.0.1", port)


def test_metrics_http_server_exposes_prometheus_samples():
    prometheus_client = pytest.importorskip("prometheus_client")
    metrics = PrometheusMetrics(registry=prometheus_client.CollectorRegistry())
    metrics.record_decision("ALLOW")
    server = start_metrics_server("127.0.0.1", 0, metrics)
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/metrics") as response:
            assert response.status == 200
            assert b'rd_guard_action_decisions_total{decision="ALLOW"} 1.0' in response.read()
    finally:
        stop_metrics_server("127.0.0.1", 0)


def test_default_prometheus_wrapper_uses_a_non_colliding_registry():
    pytest.importorskip("prometheus_client")
    first = PrometheusMetrics()
    second = PrometheusMetrics()
    first.record_decision("ALLOW")
    second.record_decision("BLOCK")

    assert b'decision="ALLOW"' in first.render()
    assert b'decision="BLOCK"' in second.render()


def test_grafana_dashboard_is_valid_json():
    path = Path(__file__).parents[1] / "examples" / "grafana" / "rd_guard_dashboard.json"
    dashboard = json.loads(path.read_text())
    assert {panel["title"] for panel in dashboard["panels"]} >= {
        "Safety state",
        "Guard action decisions / second",
        "Observe and execute latency percentiles",
        "Vault operation success rate",
    }
    latency_panel = next(
        panel for panel in dashboard["panels"] if panel["title"].endswith("latency percentiles")
    )
    quantiles = {target["expr"].split("(", 1)[1].split(",", 1)[0] for target in latency_panel["targets"]}
    assert quantiles >= {"0.50", "0.95", "0.99"}


def test_prometheus_metrics_record_guard_state_executor_and_vault(tmp_path):
    prometheus_client = pytest.importorskip("prometheus_client")
    registry = prometheus_client.CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    guard = RDGuard(metrics=metrics)

    states = (
        {"action": "noop"},
        {"action": "delete_tests"},
        {
            "action": "noop",
            "original_goal": "build safe software",
            "current_goal": "write unrelated poetry",
        },
        {"action": "noop", "context_size": 100, "context_limit": 100},
        {"action": "noop", "action_history": ["retry"] * 5, "stall_window": 5},
    )
    for state in states:
        guard.observe(state)

    machine = SafetyStateMachine(metrics=metrics)
    machine.stabilize()
    machine.stabilized()
    machine.floor_block()
    machine.retry_allowed()
    machine.enter_fault()
    from rd_guard.v11.recovery import issue_recovery_token

    machine.request_recovery(
        seal_checkpoint({"goal": "safe"}),
        issue_recovery_token("test-operator", now=1),
        now=1,
    )
    machine.enter_fault()
    with pytest.raises(RecoveryError, match="CHECKPOINT_MISSING"):
        machine.request_recovery(
            None, issue_recovery_token("test-operator", now=2), now=2
        )

    executor = GuardedExecutor(metrics=metrics)
    executor.execute({"action": "read_file"}, run=lambda action: None)

    vault = GhostVaultProduction(str(tmp_path / "rd_guard_metrics_test.log"), metrics)
    checkpoint = vault.tpm.seal({"checkpoint": "test"})
    assert vault.tpm.verify_attestation(checkpoint) is True
    assert vault.tpm.verify_attestation(
        {"data": {"checkpoint": "bad"}, "data_hash": "invalid"}
    ) is False

    assert registry.get_sample_value(
        "rd_guard_action_decisions_total", {"decision": "ALLOW"}
    ) == 2
    for decision in (
        "BLOCK",
        "FORGETTING_SIGNAL",
        "KNOWLEDGE_REDUCTION",
        "REPLAN",
    ):
        assert registry.get_sample_value(
            "rd_guard_action_decisions_total", {"decision": decision}
        ) == 1
    assert registry.get_sample_value(
        "rd_guard_state_transitions_total",
        {"from_state": "NORMAL", "to_state": "STABILIZING", "event": "STABILIZE"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_safety_state", {"state": "NORMAL"}
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_risk_score_duration_seconds_count", {"score": "combined"}
    ) == 5
    assert registry.get_sample_value("rd_guard_executor_validation_duration_seconds_count") == 1
    assert registry.get_sample_value("rd_guard_executor_execution_duration_seconds_count") == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "recovery", "outcome": "attempt"},
    ) == 2
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "recovery", "outcome": "success"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "recovery", "outcome": "failure"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "checkpoint_verification", "outcome": "success"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "checkpoint_verification", "outcome": "failure"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "checkpoint_seal", "outcome": "success"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "attestation_verification", "outcome": "success"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operations_total",
        {"operation": "attestation_verification", "outcome": "failure"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operation_duration_seconds_count",
        {"operation": "checkpoint_seal"},
    ) == 1
    assert registry.get_sample_value(
        "rd_guard_vault_operation_duration_seconds_count",
        {"operation": "checkpoint_verification"},
    ) == 2
