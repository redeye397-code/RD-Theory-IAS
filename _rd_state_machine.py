"""Explicit V10.0 safety state machine.

States
------
``NORMAL``       -- default operating state; actions are observed by RDGuard.
``STABILIZING``  -- automatic self-correction in progress (forgetting signal,
                     knowledge reduction, or replan); reversible, no operator
                     approval required.
``BLOCKED``      -- a hard IAS-floor violation was refused; the offending
                     action never executed.
``FAULT``        -- a safety-critical fault was detected (audit unavailable
                     for a high-risk action, hardware/tamper fault, etc.);
                     requires an operator-approved recovery to leave.
``RECOVERING``   -- an operator-approved recovery attempt is validating a
                     checkpoint.
``COMPROMISED``  -- terminal state reached after repeated failed recovery
                     attempts or a confirmed tamper event; requires manual,
                     out-of-band operator reset (not modeled here, by design).

Every transition below is documented in ``TRANSITION_TABLE`` with its
trigger/actor, reversibility, required evidence, whether operator approval is
required, restart behavior, repeated-recovery-attempt behavior, and behavior
when the recovery checkpoint is corrupt/missing/deleted -- see the "State
Machine" section of README.md for the human-readable table.
"""

import time

from _rd_vault_core import canonical
import hashlib


NORMAL = "NORMAL"
STABILIZING = "STABILIZING"
BLOCKED = "BLOCKED"
FAULT = "FAULT"
RECOVERING = "RECOVERING"
COMPROMISED = "COMPROMISED"

STATES = (NORMAL, STABILIZING, BLOCKED, FAULT, RECOVERING, COMPROMISED)


class InvalidTransitionError(RuntimeError):
    """Raised when an event is not valid for the machine's current state."""


class RecoveryError(RuntimeError):
    """Raised when a recovery/approval attempt is rejected."""


# (from_state, event) -> to_state
TRANSITIONS = {
    (NORMAL, "STABILIZE"): STABILIZING,
    (STABILIZING, "STABILIZE"): STABILIZING,
    (STABILIZING, "STABILIZED"): NORMAL,
    (NORMAL, "FLOOR_BLOCK"): BLOCKED,
    (STABILIZING, "FLOOR_BLOCK"): BLOCKED,
    (BLOCKED, "FLOOR_BLOCK"): BLOCKED,
    (BLOCKED, "RETRY_ALLOWED"): NORMAL,
    (NORMAL, "FAULT"): FAULT,
    (STABILIZING, "FAULT"): FAULT,
    (BLOCKED, "FAULT"): FAULT,
    (FAULT, "FAULT"): FAULT,
    (FAULT, "RECOVERY_REQUESTED"): RECOVERING,
    (RECOVERING, "RECOVERY_SUCCEEDED"): NORMAL,
    (RECOVERING, "RECOVERY_FAILED"): FAULT,
    (FAULT, "TAMPER_CONFIRMED"): COMPROMISED,
    (RECOVERING, "TAMPER_CONFIRMED"): COMPROMISED,
}

#: Human-readable transition contract. Keys mirror ``TRANSITIONS``.
TRANSITION_TABLE = {
    (NORMAL, "STABILIZE"): {
        "trigger_actor": "RDGuard (automatic) when bloat/drift/stall risk crosses threshold",
        "reversible": True,
        "evidence_required": "bloat/drift/stall risk scores recorded on the GuardAction",
        "operator_approval_required": False,
        "restart_behavior": "Resumes in STABILIZING; the next observation re-scores risk.",
        "repeated_attempt_behavior": "Unbounded; each pass is self-correcting and audited.",
        "corrupt_checkpoint_behavior": "N/A -- no recovery checkpoint is involved.",
    },
    (STABILIZING, "STABILIZED"): {
        "trigger_actor": "RDGuard (automatic) once risk falls back within thresholds",
        "reversible": True,
        "evidence_required": "post-stabilization risk scores within thresholds",
        "operator_approval_required": False,
        "restart_behavior": "If the process restarts mid-STABILIZING, it resumes in STABILIZING.",
        "repeated_attempt_behavior": "N/A -- terminal success of the stabilization loop.",
        "corrupt_checkpoint_behavior": "N/A -- no recovery checkpoint is involved.",
    },
    (NORMAL, "FLOOR_BLOCK"): {
        "trigger_actor": "IASFloor (automatic hard constraint) on a disallowed action",
        "reversible": True,
        "evidence_required": "FLOOR_BLOCK audit record with the violated rule's reason",
        "operator_approval_required": False,
        "restart_behavior": "Resumes in BLOCKED; the blocked action is never retried automatically.",
        "repeated_attempt_behavior": "Each violation re-enters BLOCKED and is independently audited.",
        "corrupt_checkpoint_behavior": "N/A -- no recovery checkpoint is involved.",
    },
    (BLOCKED, "RETRY_ALLOWED"): {
        "trigger_actor": "Caller submits a new, compliant action (automatic)",
        "reversible": True,
        "evidence_required": "the new action must independently pass the IAS floor",
        "operator_approval_required": False,
        "restart_behavior": "Resumes in BLOCKED; a compliant retry is required to return to NORMAL.",
        "repeated_attempt_behavior": "Unbounded retries are allowed; each is re-evaluated from scratch.",
        "corrupt_checkpoint_behavior": "N/A -- no recovery checkpoint is involved.",
    },
    (NORMAL, "FAULT"): {
        "trigger_actor": "System (automatic) on a safety-critical failure, e.g. audit "
        "unavailable for a high-risk action, or a hardware/tamper fault",
        "reversible": False,
        "evidence_required": "FAULT audit record with the triggering reason, if audit is available",
        "operator_approval_required": True,
        "restart_behavior": "Persisted; a restarted process resumes in FAULT, not NORMAL.",
        "repeated_attempt_behavior": "N/A -- entry transition, not a recovery attempt.",
        "corrupt_checkpoint_behavior": "N/A -- no recovery checkpoint is involved.",
    },
    (FAULT, "RECOVERY_REQUESTED"): {
        "trigger_actor": "Operator supplies a checkpoint and a single-use approval token",
        "reversible": True,
        "evidence_required": "a checkpoint whose SHA-256 hash matches its recorded data_hash",
        "operator_approval_required": True,
        "restart_behavior": "Consumed approval tokens and attempt counters persist across restarts "
        "(see to_dict/from_dict) so a restart cannot be used to replay an approval "
        "or reset the attempt counter.",
        "repeated_attempt_behavior": "Each attempt increments a bounded counter "
        "(max_recovery_attempts, default 3); exceeding it transitions to COMPROMISED.",
        "corrupt_checkpoint_behavior": "Missing (None), deleted, or corrupt (bad/mismatched hash) "
        "checkpoints are rejected; the machine returns to FAULT and the attempt is counted.",
    },
    (RECOVERING, "RECOVERY_SUCCEEDED"): {
        "trigger_actor": "System (automatic) once the checkpoint verifies and the approval is fresh",
        "reversible": True,
        "evidence_required": "valid checkpoint hash + single-use approval token not previously consumed",
        "operator_approval_required": True,
        "restart_behavior": "N/A -- terminal success of this recovery attempt.",
        "repeated_attempt_behavior": "Resets the recovery-attempt counter to zero.",
        "corrupt_checkpoint_behavior": "N/A -- only reached once the checkpoint has verified.",
    },
    (RECOVERING, "RECOVERY_FAILED"): {
        "trigger_actor": "System (automatic) when the checkpoint fails verification",
        "reversible": True,
        "evidence_required": "the failed checkpoint's verification status (missing/corrupt)",
        "operator_approval_required": True,
        "restart_behavior": "Persisted; a restarted process resumes in FAULT.",
        "repeated_attempt_behavior": "The attempt is counted toward max_recovery_attempts.",
        "corrupt_checkpoint_behavior": "Directly caused by a missing/deleted/corrupt checkpoint.",
    },
    (FAULT, "TAMPER_CONFIRMED"): {
        "trigger_actor": "System (automatic) after max_recovery_attempts is exceeded, or an "
        "explicit hardware/tamper confirmation (e.g. GhostVault poison pill)",
        "reversible": False,
        "evidence_required": "recovery-attempt count exceeding the bound, or a tamper attestation",
        "operator_approval_required": True,
        "restart_behavior": "Persisted; a restarted process resumes in COMPROMISED and cannot "
        "self-recover.",
        "repeated_attempt_behavior": "No further automated recovery attempts are accepted.",
        "corrupt_checkpoint_behavior": "N/A -- terminal state; requires manual, out-of-band reset.",
    },
}


def verify_checkpoint(checkpoint):
    """Return ``"valid"``, ``"missing"``, or ``"corrupt"`` for ``checkpoint``.

    A checkpoint of ``None`` covers both the "missing" and "deleted" cases
    described in the issue (V10.0 does not persist checkpoints as separate
    files, so there is no distinct on-disk "deleted" state to detect).
    """
    if checkpoint is None:
        return "missing"
    if not isinstance(checkpoint, dict) or "data" not in checkpoint:
        return "corrupt"
    try:
        expected_hash = hashlib.sha256(canonical(checkpoint["data"]).encode()).hexdigest()
    except (TypeError, ValueError):
        return "corrupt"
    if expected_hash != checkpoint.get("data_hash"):
        return "corrupt"
    return "valid"


def seal_checkpoint(data):
    """Create a checkpoint dict with a verifiable hash, mirroring GhostVault seals."""
    return {"data": data, "data_hash": hashlib.sha256(canonical(data).encode()).hexdigest()}


class SafetyStateMachine:
    """The explicit V10.0 safety state machine described in ``TRANSITION_TABLE``."""

    max_recovery_attempts = 3

    def __init__(
        self,
        audit_log=None,
        state=NORMAL,
        recovery_attempts=0,
        consumed_approvals=None,
        last_event_time=0.0,
    ):
        self.audit_log = audit_log if audit_log is not None else []
        self.state = state
        self.recovery_attempts = recovery_attempts
        self.consumed_approvals = set(consumed_approvals or ())
        self.last_event_time = last_event_time
        self.history = []

    def _audit(self, event, **fields):
        record = {"event": event, "state": self.state, **fields}
        try:
            self.audit_log.append(record)
        except Exception:
            # Fail-closed policy for *actions* lives in GuardedExecutor; the
            # state machine itself must never crash while recording history.
            pass
        return record

    def _transition(self, event, **fields):
        key = (self.state, event)
        if key not in TRANSITIONS:
            raise InvalidTransitionError(f"{event!r} is not valid from state {self.state!r}")
        new_state = TRANSITIONS[key]
        self.history.append((self.state, event, new_state))
        self.state = new_state
        self._audit(event, new_state=new_state, **fields)
        return self.state

    def stabilize(self, reason=""):
        return self._transition("STABILIZE", reason=reason)

    def stabilized(self):
        if self.state != STABILIZING:
            return self.state
        return self._transition("STABILIZED")

    def floor_block(self, reason=""):
        return self._transition("FLOOR_BLOCK", reason=reason)

    def retry_allowed(self):
        return self._transition("RETRY_ALLOWED")

    def enter_fault(self, reason=""):
        if self.state == FAULT:
            return self.state
        return self._transition("FAULT", reason=reason)

    def _check_clock(self, now):
        """Reject any event timestamped earlier than the last observed one.

        A rolled-back clock could otherwise be used to make an already
        consumed approval token, or an exhausted recovery attempt window,
        appear fresh again -- so this fails closed by rejecting the event
        outright rather than advancing the state machine.
        """
        if now < self.last_event_time:
            self._audit("CLOCK_ROLLBACK_DETECTED", observed=now, last=self.last_event_time)
            raise RecoveryError("CLOCK_ROLLBACK_DETECTED")
        self.last_event_time = now

    def request_recovery(self, checkpoint, approval_token, now=None):
        """Attempt a FAULT -> NORMAL recovery using ``checkpoint``.

        Raises ``InvalidTransitionError`` if not currently in ``FAULT``, or
        ``RecoveryError`` for a missing approval token, a replayed token, a
        rolled-back clock, a corrupt/missing checkpoint, or once
        ``max_recovery_attempts`` has been exceeded (which also transitions
        the machine to the terminal ``COMPROMISED`` state).
        """
        now = time.time() if now is None else now
        self._check_clock(now)

        if self.state != FAULT:
            raise InvalidTransitionError(
                f"recovery can only be requested from FAULT (current: {self.state})"
            )

        if not approval_token:
            raise RecoveryError("OPERATOR_APPROVAL_REQUIRED")

        self.recovery_attempts += 1
        if self.recovery_attempts > self.max_recovery_attempts:
            self._transition("TAMPER_CONFIRMED", reason="recovery attempts exceeded")
            raise RecoveryError("RECOVERY_ATTEMPTS_EXCEEDED")

        if approval_token in self.consumed_approvals:
            self._audit("REPLAYED_APPROVAL_REJECTED", token=approval_token)
            raise RecoveryError("REPLAYED_APPROVAL_REJECTED")

        status = verify_checkpoint(checkpoint)
        if status != "valid":
            self._transition("RECOVERY_REQUESTED", checkpoint_status=status)
            self._transition("RECOVERY_FAILED", checkpoint_status=status)
            raise RecoveryError(f"CHECKPOINT_{status.upper()}")

        self.consumed_approvals.add(approval_token)
        self._transition("RECOVERY_REQUESTED", token=approval_token)
        self._transition("RECOVERY_SUCCEEDED")
        self.recovery_attempts = 0
        return checkpoint["data"]

    def to_dict(self):
        """Serialize the durable fields needed to resume after a restart."""
        return {
            "state": self.state,
            "recovery_attempts": self.recovery_attempts,
            "consumed_approvals": sorted(self.consumed_approvals),
            "last_event_time": self.last_event_time,
        }

    @classmethod
    def from_dict(cls, data, audit_log=None):
        """Rebuild a machine from ``to_dict`` output, e.g. after a restart."""
        return cls(
            audit_log=audit_log,
            state=data.get("state", NORMAL),
            recovery_attempts=data.get("recovery_attempts", 0),
            consumed_approvals=data.get("consumed_approvals", ()),
            last_event_time=data.get("last_event_time", 0.0),
        )
