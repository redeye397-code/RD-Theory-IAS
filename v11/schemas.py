"""Reliable data models for RD Guard V11.

``Checkpoint`` and ``AgentState`` normalize the checkpoint/agent-state data
that flows through RD Guard into stable, validated shapes. Missing or
partial input data is handled gracefully via sensible defaults rather than
raising, so a malformed upstream payload never crashes the guard -- it is
instead reduced to a safe, well-typed default state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    # A single non-list value is treated as a one-item list rather than
    # rejected outright.
    return [value]


@dataclass
class Checkpoint:
    """A validated, defaulted view of a checkpoint payload."""

    original_goal: str = ""
    current_goal: str = ""
    context: List[Any] = field(default_factory=list)
    context_size: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "Checkpoint":
        data = data or {}
        context = _coerce_list(data.get("context"))
        return cls(
            original_goal=str(data.get("original_goal", "") or ""),
            current_goal=str(data.get("current_goal", "") or ""),
            context=context,
            context_size=_coerce_int(
                data.get("context_size", len(context)), default=len(context)
            ),
        )


@dataclass
class AgentState:
    """A validated, defaulted view of an agent-state payload."""

    action: Any = None
    requested_action: Any = None
    checkpoint: Checkpoint = field(default_factory=Checkpoint)
    context: List[Any] = field(default_factory=list)
    context_size: int = 0
    context_limit: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "AgentState":
        data = data or {}
        context = _coerce_list(data.get("context"))
        return cls(
            action=data.get("action"),
            requested_action=data.get("requested_action"),
            checkpoint=Checkpoint.from_dict(data.get("checkpoint")),
            context=context,
            context_size=_coerce_int(
                data.get("context_size", len(context)), default=len(context)
            ),
            context_limit=_coerce_int(data.get("context_limit", 0)),
        )

    @property
    def is_over_context_limit(self) -> bool:
        """Whether the current context size exceeds the configured limit.

        A limit of ``0`` means "no limit configured", so it never trips.
        """
        return self.context_limit > 0 and self.context_size > self.context_limit
