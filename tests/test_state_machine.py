"""Tests for the explicit V10.0 safety state machine (``SafetyStateMachine``)."""

import pytest
import secrets

from rd_executor import (
    BLOCKED,
    COMPROMISED,
    FAULT,
    NORMAL,
    STABILIZING,
    InvalidTransitionError,
    RecoveryError,
    SafetyStateMachine,
    TRANSITIONS,
    TRANSITION_TABLE,
    seal_checkpoint,
    verify_checkpoint,
)
from rd_guard.v11.recovery import issue_recovery_token


def _approval(now, ttl=900, key=None):
    return issue_recovery_token("test-operator", key=key, ttl=ttl, now=now)


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
    assert set(TRANSITIONS) == set(TRANSITION_TABLE)
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
        sm.request_recovery(
            seal_checkpoint({"a": 1}), _approval(1.0), now=1.0
        )


def test_recovery_succeeds_with_valid_checkpoint_and_fresh_approval():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    checkpoint = seal_checkpoint({"goal": "safe-state"})

    restored = sm.request_recovery(checkpoint, _approval(100.0), now=100.0)

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
        sm.request_recovery(checkpoint, _approval(100.0), now=100.0)

    assert sm.state == FAULT
    assert verify_checkpoint(checkpoint) == expected_status


def test_recovery_rejects_unsigned_operator_approval_token():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")

    with pytest.raises(RecoveryError, match="INVALID_APPROVAL_TOKEN"):
        sm.request_recovery(seal_checkpoint({"a": 1}), "", now=100.0)

    assert sm.state == FAULT


def test_replayed_approval_token_is_rejected():
    audit_log = []
    sm = SafetyStateMachine(audit_log=audit_log)
    sm.enter_fault("fault")
    checkpoint = seal_checkpoint({"a": 1})
    token = _approval(100.0)
    sm.request_recovery(checkpoint, token, now=100.0)

    sm.enter_fault("fault-again")
    with pytest.raises(RecoveryError, match="REPLAYED_APPROVAL_REJECTED"):
        sm.request_recovery(checkpoint, token, now=200.0)

    assert sm.state == FAULT
    assert all(token not in repr(record) for record in audit_log)


def test_clock_rollback_is_rejected_without_changing_state():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    sm.request_recovery(
        seal_checkpoint({"a": 1}), _approval(1000.0), now=1000.0
    )

    sm.enter_fault("fault-again")
    with pytest.raises(RecoveryError, match="CLOCK_ROLLBACK_DETECTED"):
        sm.request_recovery(
            seal_checkpoint({"a": 1}), _approval(500.0), now=500.0
        )

    assert sm.state == FAULT


def test_repeated_failed_recovery_attempts_escalate_to_compromised():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")

    for index in range(sm.max_recovery_attempts):
        with pytest.raises(RecoveryError, match="CHECKPOINT_MISSING"):
            timestamp = 100.0 + index
            sm.request_recovery(None, _approval(timestamp), now=timestamp)
        assert sm.state == FAULT

    with pytest.raises(RecoveryError, match="RECOVERY_ATTEMPTS_EXCEEDED"):
        sm.request_recovery(None, _approval(200.0), now=200.0)

    assert sm.state == COMPROMISED


def test_compromised_state_rejects_further_recovery():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    for index in range(sm.max_recovery_attempts + 1):
        try:
            timestamp = 100.0 + index
            sm.request_recovery(None, _approval(timestamp), now=timestamp)
        except RecoveryError:
            pass
    assert sm.state == COMPROMISED

    with pytest.raises(InvalidTransitionError):
        sm.request_recovery(
            seal_checkpoint({"a": 1}), _approval(500.0), now=500.0
        )


def test_compromised_state_remains_terminal_after_restart():
    sm = SafetyStateMachine(audit_log=[], state=COMPROMISED)
    restarted = SafetyStateMachine.from_dict(sm.to_dict(), audit_log=[])

    with pytest.raises(InvalidTransitionError):
        restarted.request_recovery(
            seal_checkpoint({"a": 1}), _approval(500.0), now=500.0
        )
    assert restarted.state == COMPROMISED


def test_restart_resumes_from_persisted_state_not_normal():
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    checkpoint = seal_checkpoint({"a": 1})
    token = _approval(100.0)
    sm.request_recovery(checkpoint, token, now=100.0)
    sm.enter_fault("fault-again")

    persisted = sm.to_dict()
    restarted = SafetyStateMachine.from_dict(persisted, audit_log=[])

    assert restarted.state == FAULT
    # A restart must not reset the recovery-attempt counter or forget which
    # approval tokens were already consumed (replay protection survives it).
    with pytest.raises(RecoveryError, match="REPLAYED_APPROVAL_REJECTED"):
        restarted.request_recovery(checkpoint, token, now=200.0)


@pytest.mark.parametrize(
    ("issued", "ttl", "observed", "message"),
    [
        (100.0, 10, 111.0, "APPROVAL_EXPIRED"),
        (200.0, 10, 100.0, "APPROVAL_NOT_YET_VALID"),
    ],
)
def test_expired_and_future_recovery_tokens_are_rejected(issued, ttl, observed, message):
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    with pytest.raises(RecoveryError, match=message):
        sm.request_recovery(
            seal_checkpoint({"a": 1}),
            _approval(issued, ttl=ttl),
            now=observed,
        )
    assert sm.recovery_attempts == 1


def test_tampered_and_wrong_key_tokens_are_rejected():
    import base64
    import json

    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    token = _approval(100.0)
    replacement = "A" if token[-1] != "A" else "B"
    with pytest.raises(RecoveryError, match="INVALID_APPROVAL_SIGNATURE"):
        sm.request_recovery(seal_checkpoint({"a": 1}), token[:-1] + replacement, now=100.0)

    encoded, signature = token.split(".")
    payload = json.loads(
        base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    )
    payload["operator"] = "tampered-operator"
    altered = base64.urlsafe_b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    with pytest.raises(RecoveryError, match="INVALID_APPROVAL_SIGNATURE"):
        sm.request_recovery(
            seal_checkpoint({"a": 1}), f"{altered}.{signature}", now=100.0
        )

    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    token = _approval(100.0, key=secrets.token_hex(32))
    with pytest.raises(RecoveryError, match="INVALID_APPROVAL_SIGNATURE"):
        sm.request_recovery(seal_checkpoint({"a": 1}), token, now=100.0)


def test_wrong_scope_and_malformed_tokens_are_rejected():
    import base64
    import hashlib
    import hmac
    import json
    import os

    from rd_guard.v11.recovery import RecoveryTokenError, verify_recovery_token

    encoded, _signature = _approval(100.0).split(".")
    payload = json.loads(
        base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    )
    payload["purpose"] = "other"
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    key = os.environ["RD_RECOVERY_KEY"].encode()
    signature = hmac.new(key, encoded.encode("ascii"), hashlib.sha256).digest()
    token = f"{encoded}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"

    with pytest.raises(RecoveryTokenError, match="INVALID_APPROVAL_SCOPE"):
        verify_recovery_token(token, now=100.0)
    with pytest.raises(RecoveryTokenError, match="INVALID_APPROVAL_TOKEN"):
        verify_recovery_token("not-a-signed-token", now=100.0)

    claims = verify_recovery_token(_approval(100.0), now=100.0)
    assert set(claims) >= {"operator", "jti", "iat", "exp", "purpose"}


def test_missing_recovery_key_fails_closed(monkeypatch):
    sm = SafetyStateMachine(audit_log=[])
    sm.enter_fault("fault")
    token = _approval(100.0)
    monkeypatch.delenv("RD_RECOVERY_KEY")

    with pytest.raises(RecoveryError, match="RD_RECOVERY_KEY is missing or too short"):
        sm.request_recovery(seal_checkpoint({"a": 1}), token, now=100.0)

    assert sm.state == FAULT
    assert sm.recovery_attempts == 1


def test_checkpoint_hmac_rejects_recomputed_plain_hash():
    import hashlib

    from _rd_vault_core import canonical

    checkpoint = seal_checkpoint({"a": 1})
    checkpoint["data"] = {"a": "attacker replacement"}
    checkpoint["data_hash"] = hashlib.sha256(canonical(checkpoint["data"]).encode()).hexdigest()

    assert verify_checkpoint(checkpoint) == "corrupt"


def test_hash_only_legacy_checkpoint_is_rejected():
    import hashlib

    from _rd_vault_core import canonical

    checkpoint = {
        "data": {"a": 1},
        "data_hash": hashlib.sha256(canonical({"a": 1}).encode()).hexdigest(),
    }
    assert verify_checkpoint(checkpoint) == "corrupt"


def test_missing_checkpoint_key_fails_closed(monkeypatch):
    checkpoint = seal_checkpoint({"a": 1})
    monkeypatch.delenv("RD_CHECKPOINT_KEY")

    with pytest.raises(ValueError, match="RD_CHECKPOINT_KEY is missing or too short"):
        verify_checkpoint(checkpoint)


def test_short_signing_keys_fail_closed(monkeypatch):
    from rd_guard.v11.recovery import RecoveryTokenError

    monkeypatch.setenv("RD_RECOVERY_KEY", "weak")
    monkeypatch.setenv("RD_CHECKPOINT_KEY", "weak")

    with pytest.raises(RecoveryTokenError, match="RD_RECOVERY_KEY is missing or too short"):
        _approval(100.0)
    with pytest.raises(ValueError, match="RD_CHECKPOINT_KEY is missing or too short"):
        seal_checkpoint({"a": 1})


def test_audit_write_failure_does_not_crash_transitions():
    class ExplodingAudit(list):
        def append(self, record):
            raise OSError("disk full")

    sm = SafetyStateMachine(audit_log=ExplodingAudit())
    sm.stabilize()
    assert sm.state == STABILIZING
