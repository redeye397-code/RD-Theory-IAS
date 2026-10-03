"""Canonical action schema shared by the supported V11 guard APIs."""

from dataclasses import dataclass

from rd_guard.v11.policy import normalize_action_name


class SchemaError(ValueError):
    """Raised when an action does not conform to the canonical schema."""


VALID_RISK_LEVELS = ("low", "medium", "high")


@dataclass(frozen=True)
class CanonicalAction:
    """The canonical, validated representation of an agent action."""

    type: str
    target: str = ""
    path: str = ""
    resource: str = ""
    command: str = ""
    branch: str = ""
    ci_passed: object = False
    risk_level: str = "low"

    def __post_init__(self):
        if not isinstance(self.type, str) or not normalize_action_name(self.type):
            raise SchemaError("action.type is required and must be a non-empty string")
        if self.risk_level not in VALID_RISK_LEVELS:
            raise SchemaError(
                f"action.risk_level must be one of {VALID_RISK_LEVELS}, "
                f"got {self.risk_level!r}"
            )

    @classmethod
    def from_state(cls, agent_state):
        """Build a canonical action from a bare action or agent-state mapping."""
        if isinstance(agent_state, cls):
            return agent_state

        has_action_field = isinstance(agent_state, dict) and (
            "action" in agent_state or "requested_action" in agent_state
        )
        if isinstance(agent_state, dict):
            state = agent_state
            raw_action = (
                agent_state.get("action", agent_state.get("requested_action"))
                if has_action_field else None
            )
        else:
            state = {}
            raw_action = agent_state

        if isinstance(raw_action, cls):
            return raw_action
        if raw_action is None and not has_action_field:
            raise SchemaError("action type is required")
        if isinstance(raw_action, dict):
            data = dict(raw_action)
            action_type = data.get("type", data.get("name"))
        elif isinstance(raw_action, str):
            data = {}
            action_type = raw_action
        else:
            raise SchemaError("action must be a string, a dict with a 'type'/'name', or a CanonicalAction")

        if not isinstance(action_type, str) or not normalize_action_name(action_type):
            raise SchemaError("action must declare a non-empty string 'type' (or 'name')")

        def field(name):
            return data.get(name, state.get(name, ""))

        ci_passed = data.get("ci_passed", state.get("ci_passed", state.get("ci", False)))
        risk_level = data.get("risk_level", state.get("risk_level", "low"))
        return cls(
            type=action_type,
            target=str(field("target")),
            path=str(field("path")),
            resource=str(field("resource")),
            command=str(field("command")),
            branch=str(field("branch")),
            ci_passed=ci_passed,
            risk_level=str(risk_level),
        )

    def as_text(self):
        """Return the shared normalized representation of the action fields."""
        return "_".join(
            normalize_action_name(part)
            for part in (
                self.type, self.target, self.path, self.resource,
                self.command, self.branch,
            )
            if part
        )
