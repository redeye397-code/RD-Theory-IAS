"""Tests for the explicit V10.0 safety state machine (``SafetyStateMachine``)."""

import pytest

from rd_executor import (
    BLOCKED,
    COMPROMISED,
    FAULT,
    NORMAL,
    RECOVERING,
    STABILIZING,
    InvalidTransitionError,
    RecoveryError,
    SafetyStateMachine,
    TRANSITION_TABLE,
    seal_checkpoint,
    verify_checkpoint,
)


REQUIRED_TRANSITION_FIELDS = (
    "trigger_actor",
    "reversible",
    "evidence_required",
    "operator_approval_required",
    "restart_behavior",
    "repeated_attempt_behavior",
    "corrupt_checkpoint_behavior",
)


def test_every_transition_is_fully_documented():
    for key, contract in TRANSITION_TABLE.items():
        for field_name in REQUIRED_TRANSITION_FIELDS:
            assert field_name in contract, f"{key} missing {field_name}"
            assert contract[field_name] != "", f"{key} has empty {field_name}"


def test_stabilize_and_stabilized_round_trip():
    sm = SafetyStateMachine(audit_log=[])
    assert sm.state == NORMAL

    sm.stabilize(reason="drift")
    assert sm.state == STABILIZING

    sm.stabilized()
    assert sm.state == NORMAL


def test_stabilized_is_a_noop_outside_stabilizing():
    sm = SafetyStateMachine(audit_log=[])
    assert sm.stabilized() == NORMAL


def test_floor_block_and_retry_allowed():
    sm = SafetyStateMachine(audit_log=[])
    sm.floor_block(reason="deleting tests is prohibited")
    assert sm.state == BLOCKED

    sm.retry_allowed()
    assert sm.state == NORMAL


def test_enter_fault_from_any_operating_state():
    for setup in (
        lambda sm: None,
        lambda sm: sm.stabilize(),
        lambda sm: sm.floor_block(),
    ):
        sm = SafetyStateMachine(audit_log=[])
        setup(sm)
        sm.enter_fault(reason="audit unavailable")
        assert sm.state == FAULT


def test_enter_fault_is_idempotent():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("first")
    sm.enter_fault("second")
    assert sm.state == FAULT


def test_enter_fault_records_repeated_triggers_instead_of_dropping_them():
    audit_log = []
    sm = SafetyStateMachine(audit_log=audit_log)
    sm.enter_fault("first")
    sm.enter_fault("second")

    fault_records = [record for record in audit_log if record["event"] == "FAULT"]
    assert len(fault_records) == 2
    assert fault_records[0]["reason"] == "first"
    assert fault_records[1]["reason"] == "second"



def test_invalid_transition_raises():
    sm = SafetyStateMachine(audit_log=[])
    with pytest.raises(InvalidTransitionError):
        sm.request_recovery(seal_checkpoint({"a": 1}), "tok", now=1.0)


def test_recovery_succeeds_with_valid_checkpoint_and_fresh_approval():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    checkpoint = seal_checkpoint({"goal": "safe-state"})

    restored = sm.request_recovery(checkpoint, "approval-1", now=100.0)

    assert restored == {"goal": "safe-state"}
    assert sm.state == NORMAL
    assert sm.recovery_attempts == 0


@pytest.mark.parametrize(
    "checkpoint, expected_status",
    [
        (None, "missing"),
        ({}, "corrupt"),
        ({"data": {"a": 1}, "data_hash": "0" * 64}, "corrupt"),
    ],
)
def test_recovery_rejects_missing_or_corrupt_checkpoints(checkpoint, expected_status):
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")

    with pytest.raises(RecoveryError, match=f"CHECKPOINT_{expected_status.upper()}"):
        sm.request_recovery(checkpoint, "approval-1", now=100.0)

    assert sm.state == FAULT
    assert verify_checkpoint(checkpoint) == expected_status


def test_recovery_requires_operator_approval_token():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")

    with pytest.raises(RecoveryError, match="OPERATOR_APPROVAL_REQUIRED"):
        sm.request_recovery(seal_checkpoint({"a": 1}), "", now=100.0)

    assert sm.state == FAULT


def test_replayed_approval_token_is_rejected():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    checkpoint = seal_checkpoint({"a": 1})
    sm.request_recovery(checkpoint, "reuse-me", now=100.0)

    sm.enter_fault("fault-again")
    with pytest.raises(RecoveryError, match="REPLAYED_APPROVAL_REJECTED"):
        sm.request_recovery(checkpoint, "reuse-me", now=200.0)

    assert sm.state == FAULT


def test_clock_rollback_is_rejected_without_changing_state():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    sm.request_recovery(seal_checkpoint({"a": 1}), "tok-1", now=1000.0)

    sm.enter_fault("fault-again")
    with pytest.raises(RecoveryError, match="CLOCK_ROLLBACK_DETECTED"):
        sm.request_recovery(seal_checkpoint({"a": 1}), "tok-2", now=500.0)

    assert sm.state == FAULT


def test_repeated_failed_recovery_attempts_escalate_to_compromised():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")

    for index in range(sm.max_recovery_attempts):
        with pytest.raises(RecoveryError, match="CHECKPOINT_MISSING"):
            sm.request_recovery(None, f"tok-{index}", now=100.0 + index)
        assert sm.state == FAULT

    with pytest.raises(RecoveryError, match="RECOVERY_ATTEMPTS_EXCEEDED"):
        sm.request_recovery(None, "tok-final", now=200.0)

    assert sm.state == COMPROMISED


def test_compromised_state_rejects_further_recovery():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    for index in range(sm.max_recovery_attempts + 1):
        try:
            sm.request_recovery(None, f"tok-{index}", now=100.0 + index)
        except RecoveryError:
            pass
    assert sm.state == COMPROMISED

    with pytest.raises(InvalidTransitionError):
        sm.request_recovery(seal_checkpoint({"a": 1}), "tok-new", now=500.0)


def test_restart_resumes_from_persisted_state_not_normal():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    checkpoint = seal_checkpoint({"a": 1})
    sm.request_recovery(checkpoint, "consumed-token", now=100.0)
    sm.enter_fault("fault-again")

    persisted = sm.to_dict()
    restarted = SafetyStateMachine.from_dict(persisted, audit_log=[])

    assert restarted.state == FAULT
    # A restart must not reset the recovery-attempt counter or forget which
    # approval tokens were already consumed (replay protection survives it).
    with pytest.raises(RecoveryError, match="REPLAYED_APPROVAL_REJECTED"):
        restarted.request_recovery(checkpoint, "consumed-token", now=200.0)


def test_audit_write_failure_does_not_crash_transitions():
    class ExplodingAudit(list):
        def append(self, record):
            raise OSError("disk full")

    sm = SafetyStateMachine(audit_log=ExplodingAudit())
    sm.stabilize()
    assert sm.state == STABILIZING
