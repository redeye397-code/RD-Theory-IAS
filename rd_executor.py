"""RD-Executor V10: the canonical GuardedExecutor enforcement boundary.

Stable import path:

    from rd_executor import GuardedExecutor
    from rd_guard import RDGuard

``GuardedExecutor`` is the single point through which agent actions must
pass: it validates the canonical action schema, observes the action with
``RDGuard``, tracks the explicit safety state machine, and fails closed
(blocking the action) when the audit log is unavailable for a high-risk
action.
"""

from _rd_guard_executor import GuardedExecutor, HIGH_RISK_KEYWORDS
from _rd_guard_schema import CanonicalAction, SchemaError
from _rd_state_machine import (
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

__all__ = [
    "GuardedExecutor",
    "HIGH_RISK_KEYWORDS",
    "CanonicalAction",
    "SchemaError",
    "SafetyStateMachine",
    "TRANSITION_TABLE",
    "InvalidTransitionError",
    "RecoveryError",
    "verify_checkpoint",
    "seal_checkpoint",
    "NORMAL",
    "STABILIZING",
    "BLOCKED",
    "FAULT",
    "RECOVERING",
    "COMPROMISED",
]
