"""Tests for ``GuardedExecutor``, the V10.0 enforcement boundary."""

import pytest

from _rd_guard_actions import AuditSink
from rd_executor import CanonicalAction, GuardedExecutor, SchemaError


def test_low_risk_allowed_action_runs_and_reaches_run_callback():
    executor = GuardedExecutor()
    executed = []

    result = executor.execute({"action": "read_file", "path": "README.md"}, run=executed.append)

    assert result.decision == "ALLOW"
    assert executed and executed[0].type == "read_file"
    assert executor.state_machine.state == "NORMAL"


def test_high_risk_floor_blocked_action_never_reaches_run_callback():
    executor = GuardedExecutor()
    executed = []

    result = executor.execute({"action": "delete_tests"}, run=executed.append)

    assert result.decision == "BLOCK"
    assert result.blocked is True
    assert executed == []
    assert executor.state_machine.state == "BLOCKED"


def test_invalid_action_schema_raises_before_execution():
    executor = GuardedExecutor()
    executed = []

    with pytest.raises(SchemaError):
        executor.execute({"action": {}}, run=executed.append)

    assert executed == []


def test_audit_unavailable_fails_closed_for_high_risk_action():
    audit = AuditSink(backend=[])
    executor = GuardedExecutor(audit_log=audit)
    executed = []
    audit.mark_unavailable(True)

    result = executor.execute({"action": "push", "branch": "main", "ci_passed": True}, run=executed.append)

    assert result.decision == "BLOCK"
    assert result.blocked is True
    assert executed == []
    assert executor.state_machine.state == "FAULT"


def test_audit_unavailable_does_not_block_low_risk_actions():
    audit = AuditSink(backend=[])
    executor = GuardedExecutor(audit_log=audit)
    executed = []
    audit.mark_unavailable(True)

    result = executor.execute({"action": "read_file"}, run=executed.append)

    assert result.decision == "ALLOW"
    assert executed
    assert executor.state_machine.state == "NORMAL"


def test_stabilizing_decision_transitions_state_machine_and_still_runs():
    executor = GuardedExecutor()
    executed = []

    state = {"action_history": ["retry"] * 5, "stall_window": 5}
    result = executor.execute(state, run=executed.append)

    assert result.decision == "REPLAN"
    assert executor.state_machine.state == "STABILIZING"
    assert executed


def test_stabilizing_returns_to_normal_once_risk_clears():
    executor = GuardedExecutor()

    stalled_state = {"action_history": ["retry"] * 5, "stall_window": 5}
    executor.execute(stalled_state)
    assert executor.state_machine.state == "STABILIZING"

    calm_state = {"action": "noop"}
    executor.execute(calm_state)
    assert executor.state_machine.state == "NORMAL"


def test_high_risk_action_cannot_bypass_executor_via_risk_level():
    executor = GuardedExecutor()
    executed = []

    result = executor.execute(
        {"action": {"type": "innocuous_name", "risk_level": "high"}}, run=executed.append
    )

    # Not blocked by the IAS floor keyword match, but still recognized as
    # high-risk by the executor's own schema-aware classification.
    assert executor._is_high_risk(CanonicalAction.from_state(
        {"action": {"type": "innocuous_name", "risk_level": "high"}}
    ))
    assert result.decision == "ALLOW"
    assert executed
