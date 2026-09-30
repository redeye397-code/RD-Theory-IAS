"""Compatibility exports for the archived V9 risk helpers."""

import warnings

warnings.warn(
    "risk_engine_v9 is archived; use the supported API from rd_guard.",
    DeprecationWarning,
    stacklevel=2,
)

from _rd_guard_risk_engine import (
    bloat_score,
    combined_risk,
    drift_score,
    stall_score,
)

__all__ = ["bloat_score", "combined_risk", "drift_score", "stall_score"]
