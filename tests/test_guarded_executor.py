"""Tests for ``GuardedExecutor``, the V10.0 enforcement boundary."""

import pytest

from _rd_guard_actions import AuditSink
from rd_executor import CanonicalAction, GuardedExecutor
from rd_guard.v11.policy import READ_ONLY_ACTIONS


def test_low_risk_allowed_action_runs_and_reaches_run_callback():
    executor = GuardedExecutor()
    executed = []

    result = executor.execute({"action": "read_file", "path": "README.md"}, run=executed.append)

    assert result.decision == "ALLOW"
    assert executed and executed[0].type == "read_file"
    assert executor.state_machine.state == "NORMAL"


@pytest.mark.parametrize("action_type", sorted(READ_ONLY_ACTIONS))
def test_allowlisted_read_only_actions_remain_allowed(action_type):
    result = GuardedExecutor().execute({"action": action_type})

    assert result.decision != "BLOCK"
    assert result.blocked is False


def test_canonical_action_objects_use_the_same_allowlist():
    action = CanonicalAction.from_state("read_file")
    result = GuardedExecutor().execute({"action": action})

    assert result.decision == "ALLOW"
    assert result.blocked is False


@pytest.mark.parametrize("state", ["FAULT", "RECOVERING", "COMPROMISED"])
def test_non_operational_safety_states_never_execute_actions(state):
    from _rd_state_machine import SafetyStateMachine

    machine = SafetyStateMachine(state=state)
    executor = GuardedExecutor(state_machine=machine)
    executed = []
    result = executor.execute({"action": "read_file"}, run=executed.append)

    assert result.decision == "BLOCK"
    assert result.blocked
    assert executed == []
    assert machine.state == state


def test_high_risk_keyword_matching_avoids_substring_false_positives():
    executor = GuardedExecutor()

    # "confirm_receipt" contains "rm" and "dropdown_menu" contains "drop" as
    # plain substrings, but neither is the high-risk word itself.
    assert executor._is_high_risk(CanonicalAction.from_state({"action": "confirm_receipt"})) is False
    assert executor._is_high_risk(CanonicalAction.from_state({"action": "render_dropdown_menu"})) is False
    assert executor._is_high_risk(CanonicalAction.from_state({"action": "rm_tests_file"})) is True
    assert executor._is_high_risk(CanonicalAction.from_state({"action": "drop", "path": "table"})) is True


def test_high_risk_floor_blocked_action_never_reaches_run_callback():
    executor = GuardedExecutor()
    executed = []

    result = executor.execute({"action": "delete_tests"}, run=executed.append)

    assert result.decision == "BLOCK"
    assert result.blocked is True
    assert executed == []
    assert executor.state_machine.state == "BLOCKED"


def test_invalid_action_schema_is_blocked_before_execution():
    executor = GuardedExecutor()
    executed = []

    result = executor.execute({"action": {}}, run=executed.append)

    assert result.decision == "BLOCK"
    assert result.blocked
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


def test_audit_backend_write_failure_fails_closed_for_high_risk_action():
    class DiskFullAudit(list):
        def append(self, record):
            raise OSError("disk full")

    executor = GuardedExecutor(audit_log=DiskFullAudit())
    executed = []

    result = executor.execute(
        {"action": {"type": "publish", "risk_level": "high"}},
        run=executed.append,
    )

    assert result.decision == "BLOCK"
    assert result.blocked is True
    assert executed == []
    assert executor.state_machine.state == "FAULT"


def test_audit_failure_while_recording_floor_block_fails_closed():
    class AuditFailsOnBlock(list):
        def append(self, record):
            if record.get("event") == "FLOOR_BLOCK":
                raise OSError("disk full")
            super().append(record)

    executor = GuardedExecutor(audit_log=AuditFailsOnBlock())
    executed = []

    result = executor.execute({"action": "delete_tests"}, run=executed.append)

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


def test_audit_unavailable_blocks_every_mutating_action():
    audit = AuditSink(backend=[])
    executor = GuardedExecutor(audit_log=audit)
    executed = []
    audit.mark_unavailable(True)

    result = executor.execute({"action": "write_file"}, run=executed.append)

    assert result.decision == "BLOCK"
    assert result.blocked
    assert executed == []
    assert executor.state_machine.state == "FAULT"


def test_stabilizing_decision_transitions_state_machine_and_still_runs():
    executor = GuardedExecutor()
    executed = []

    state = {"action": "replan", "action_history": ["retry"] * 5, "stall_window": 5}
    result = executor.execute(state, run=executed.append)

    assert result.decision == "REPLAN"
    assert executor.state_machine.state == "STABILIZING"
    assert executed


def test_stabilizing_returns_to_normal_once_risk_clears():
    executor = GuardedExecutor()

    stalled_state = {
        "action": "replan",
        "action_history": ["retry"] * 5,
        "stall_window": 5,
    }
    executor.execute(stalled_state)
    assert executor.state_machine.state == "STABILIZING"

    calm_state = {"action": "noop"}
    executor.execute(calm_state)
    assert executor.state_machine.state == "NORMAL"


def test_unknown_high_risk_action_is_blocked_by_default():
    executor = GuardedExecutor()
    executed = []

    result = executor.execute(
        {"action": {"type": "innocuous_name", "risk_level": "high"}}, run=executed.append
    )

    assert executor._is_high_risk(CanonicalAction.from_state(
        {"action": {"type": "innocuous_name", "risk_level": "high"}}
    ))
    assert result.decision == "BLOCK"
    assert result.blocked
    assert executed == []


@pytest.mark.parametrize(
    "action",
    [
        "unlink",
        "erase",
        "rmtree",
        "truncate",
        "wipe",
        "purge",
        "shred",
        "DeLeTe_TeStS",
        "deleteTests",
        "dｅlete_tests",
        "delete\u200b_tests",
        "dеleteTests",
        "delete/tests",
        {"type": "read_file", "metadata": {"operation": "shred"}},
        {"type": "read_file", "metadata": {"shred": True}},
        {"type": "read_file", "command": "git push --force"},
        {"type": "read_file", "metadata": {"operation": "publish"}},
        42,
        {"type": 42},
    ],
)
def test_adversarial_and_unknown_actions_never_reach_run(action):
    executor = GuardedExecutor()
    executed = []

    result = executor.execute({"action": action}, run=executed.append)

    assert result.decision == "BLOCK"
    assert result.blocked
    assert result.reason
    assert executed == []


def test_unknown_action_is_audited_with_deny_reason():
    executor = GuardedExecutor()
    result = executor.execute({"action": "brand_new_action"})

    assert result.decision == "BLOCK"
    assert "Unknown action" in result.reason
    assert result.audit_record["reason"] == result.reason
