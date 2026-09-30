"""Compatibility exports for archived V9 action helpers."""

import warnings

warnings.warn(
    "actions_v9 is archived; use the supported V10 API from rd_guard.",
    DeprecationWarning,
    stacklevel=2,
)

from _rd_guard_actions import (
    AUDIT_LOG,
    floor_block,
    forgetting_signal,
    knowledge_reduction,
)

__all__ = ["AUDIT_LOG", "floor_block", "forgetting_signal", "knowledge_reduction"]
