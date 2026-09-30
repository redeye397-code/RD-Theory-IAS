"""Compatibility exports for the archived RD-Guard V9 import path."""

import warnings

warnings.warn(
    "rd_guard_v9 is archived; import RDGuard from rd_guard instead.",
    DeprecationWarning,
    stacklevel=2,
)

from rd_guard import AgentState, GuardAction, IASFloor, RDGuard

__all__ = ["AgentState", "GuardAction", "IASFloor", "RDGuard"]
