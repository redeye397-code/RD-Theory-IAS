"""Canonical action schema for the V10.0 core safety contract.

``CanonicalAction`` normalizes the many ad-hoc shapes an ``agent_state``'s
action may take (a bare string, a ``{"type": ..., "target": ...}`` dict, or
the legacy ``requested_action`` field) into one validated representation.
``GuardedExecutor`` (see ``_rd_guard_executor.py``) requires every action to
pass through this schema before it is observed or executed, so malformed or
untyped actions are rejected rather than silently treated as low risk.
"""

from dataclasses import dataclass


class SchemaError(ValueError):
    """Raised when an action does not conform to the canonical schema."""


VALID_RISK_LEVELS = ("low", "medium", "high")

_CI_PASSED_TRUE_STRINGS = {"passed", "success", "green"}


def _coerce_ci_passed(value):
    """Coerce the many V9-era CI-status shapes into a canonical bool.

    Mirrors ``IASFloor.check``'s own tolerant handling of ``ci_passed``/``ci``
    (``True``, or a string like ``"passed"``/``"success"``/``"green"``, or a
    ``{"passed": ...}`` dict) so the canonical schema stays consistent with
    the existing enforcement logic instead of silently accepting arbitrary
    values.
    """
    if isinstance(value, dict):
        value = value.get("passed", False)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _CI_PASSED_TRUE_STRINGS
    return bool(value)


@dataclass(frozen=True)
class CanonicalAction:
    """The canonical, validated representation of an agent action."""

    type: str
    target: str = ""
    path: str = ""
    resource: str = ""
    command: str = ""
    branch: str = ""
    ci_passed: bool = False
    risk_level: str = "low"

    def __post_init__(self):
        if not isinstance(self.type, str) or not self.type.strip():
            raise SchemaError("action.type is required and must be a non-empty string")
        if self.risk_level not in VALID_RISK_LEVELS:
            raise SchemaError(
                f"action.risk_level must be one of {VALID_RISK_LEVELS}, "
                f"got {self.risk_level!r}"
            )
        if not isinstance(self.ci_passed, bool):
            object.__setattr__(self, "ci_passed", _coerce_ci_passed(self.ci_passed))

    @classmethod
    def from_state(cls, agent_state):
        """Build a ``CanonicalAction`` from an ``agent_state`` dict or action.

        Accepts a bare action string/dict (as already used throughout the
        V9-era guard code) as well as a full ``agent_state`` dict with an
        ``action``/``requested_action`` field, and raises ``SchemaError``
        when no action type can be determined.
        """
        if isinstance(agent_state, cls):
            return agent_state

        has_action_field = isinstance(agent_state, dict) and (
            "action" in agent_state or "requested_action" in agent_state
        )

        if isinstance(agent_state, dict):
            state = agent_state
            raw_action = (
                agent_state.get("action", agent_state.get("requested_action"))
                if has_action_field
                else None
            )
        else:
            state = {}
            raw_action = agent_state

        if isinstance(raw_action, cls):
            return raw_action

        if raw_action is None and not has_action_field:
            # No action was declared at all (e.g. a pure risk-observation
            # state); default to a generic, low-risk placeholder rather than
            # rejecting states that never claimed to carry an action.
            data = {}
            action_type = "unspecified"
        elif isinstance(raw_action, dict):
            data = dict(raw_action)
            action_type = data.get("type", data.get("name"))
        elif isinstance(raw_action, str):
            data = {}
            action_type = raw_action
        else:
            raise SchemaError(
                "action must be a string, a dict with a 'type'/'name', or a "
                "CanonicalAction"
            )

        if not action_type:
            raise SchemaError("action must declare a non-empty 'type' (or 'name')")


        def field(name):
            return data.get(name, state.get(name, ""))

        ci_passed = data.get(
            "ci_passed", state.get("ci_passed", state.get("ci", False))
        )
        risk_level = data.get("risk_level", state.get("risk_level", "low"))

        return cls(
            type=str(action_type),
            target=str(field("target")),
            path=str(field("path")),
            resource=str(field("resource")),
            command=str(field("command")),
            branch=str(field("branch")),
            ci_passed=ci_passed,
            risk_level=str(risk_level),
        )

    def as_text(self):
        """A lowercase, normalized, ``_``-delimited token stream for keyword matching."""
        parts = (
            self.type,
            self.target,
            self.path,
            self.resource,
            self.command,
            self.branch,
        )
        return "_".join(
            str(part).lower().replace("-", "_").replace(" ", "_") for part in parts
        )
