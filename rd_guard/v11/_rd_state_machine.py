"""Compatibility re-export of the authoritative root state machine."""

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
    TRANSITIONS,
    TRANSITION_TABLE,
    seal_checkpoint,
    verify_checkpoint,
)

__all__ = [
    "BLOCKED",
    "COMPROMISED",
    "FAULT",
    "NORMAL",
    "RECOVERING",
    "STABILIZING",
    "InvalidTransitionError",
    "RecoveryError",
    "SafetyStateMachine",
    "TRANSITIONS",
    "TRANSITION_TABLE",
    "seal_checkpoint",
    "verify_checkpoint",
]
