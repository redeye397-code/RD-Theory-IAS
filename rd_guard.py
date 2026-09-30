"""RD-Guard V10: the canonical agent-loop stability governor API."""

from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from _rd_guard_actions import floor_block, forgetting_signal, knowledge_reduction
from _rd_guard_risk_engine import (
    bloat_score,
    combined_risk,
    drift_score,
    stall_score,
)


class AgentState(TypedDict, total=False):
    """Dictionary fields consumed or updated by the V9 governor."""

    action: Any
    requested_action: Any
    branch: str
    ci_passed: Any
    ci: Any
    deleting_tests: bool
    bypass_alignment: bool
    alignment_prompt_bypassed: bool
    context: Any
    context_size: int
    context_limit: int
    tool_calls: Any
    tool_call_limit: int
    tool_call_history: Any
    target: Any
    path: Any
    resource: Any
    command: Any
    original_goal: str
    current_goal: str
    goal_drift: float
    drift_score: float
    action_history: Any
    actions: Any
    stall_window: int
    no_progress_steps: int
    no_progress_limit: int
    stalled: bool
    checkpoint: dict


@dataclass(frozen=True)
class GuardAction:
    decision: Literal[
        "ALLOW", "BLOCK", "FORGETTING_SIGNAL", "KNOWLEDGE_REDUCTION", "REPLAN"
    ]
    action: object = None
    reason: str = ""
    risk: float = 0.0
    bloat_score: float = 0.0
    drift_score: float = 0.0
    stall_score: float = 0.0
    blocked: bool = False
    audit_record: dict = None


class IASFloor:
    """Hard constraints for agent actions with direct safety implications."""

    def check(self, agent_state):
        action = agent_state.get("action", agent_state.get("requested_action", ""))
        action_fields = []
        action_branch = ""
        action_data = action if isinstance(action, dict) else None
        if isinstance(action, dict):
            action_branch = action.get("branch", "")
            action_fields.extend(
                action.get(key, "")
                for key in (
                    "type",
                    "name",
                    "target",
                    "path",
                    "resource",
                    "command",
                    "branch",
                )
            )
            action = action.get("type", action.get("name", ""))
        action_fields.extend(
            agent_state.get(key, "")
            for key in ("target", "path", "resource", "command")
        )
        action_text = " ".join(
            str(value).lower().replace("-", "_").replace(" ", "_")
            for value in (action, *action_fields)
        )

        if (
            agent_state.get("deleting_tests")
            or (
                "test" in action_text
                and any(
                    word in action_text
                    for word in ("delete", "remove", "rm_", "unlink", "erase", "drop")
                )
            )
        ):
            return "Deleting tests is prohibited by the IAS floor"

        branch = str(agent_state.get("branch", action_branch)).lower()
        branch = branch.rstrip("/").rsplit("/", 1)[-1]
        pushes_main = "push" in action_text and (
            "main" in action_text or branch == "main"
        )
        ci = agent_state.get("ci_passed", agent_state.get("ci", False))
        if action_data is not None:
            ci = agent_state.get(
                "ci_passed",
                agent_state.get("ci", action_data.get("ci_passed", False)),
            )
        if isinstance(ci, dict):
            ci = ci.get("passed", False)
        ci_passed = ci is True or (
            isinstance(ci, str) and ci.strip().lower() in {"passed", "success", "green"}
        )
        if pushes_main and not ci_passed:
            return "Pushing to main requires passing CI"

        if (
            agent_state.get("bypass_alignment")
            or agent_state.get("alignment_prompt_bypassed")
            or any(
                phrase in action_text
                for phrase in (
                    "bypass_alignment",
                    "skip_alignment",
                    "ignore_alignment",
                )
            )
        ):
            return "Bypassing alignment prompts is prohibited by the IAS floor"
        return None


class RDGuard:
    """Observe agent state, enforce hard floors, and recommend stabilization."""

    def __init__(
        self,
        floor=None,
        audit_log=None,
        bloat_threshold=0.7,
        drift_threshold=0.6,
        stall_threshold=0.6,
    ):
        self.floor = floor or IASFloor()
        self.audit_log = audit_log if audit_log is not None else []
        self.bloat_threshold = bloat_threshold
        self.drift_threshold = drift_threshold
        self.stall_threshold = stall_threshold

    def observe(self, agent_state: AgentState) -> GuardAction:
        """Return a BLOCK, stabilization recommendation, or ALLOW result."""
        if not isinstance(agent_state, dict):
            raise TypeError("agent_state must be a dictionary")

        reason = self.floor.check(agent_state)
        if reason:
            result = floor_block(reason, self.audit_log)
            return GuardAction(
                decision=result["decision"],
                action=agent_state.get("action", agent_state.get("requested_action")),
                reason=result["reason"],
                blocked=result["blocked"],
                audit_record=result["audit_record"],
            )

        bloat = bloat_score(agent_state)
        drift = drift_score(agent_state)
        stall = stall_score(agent_state)
        risk = combined_risk(agent_state)
        action = agent_state.get("action", agent_state.get("requested_action"))

        if drift >= self.drift_threshold:
            checkpoint = agent_state.get("checkpoint")
            if isinstance(checkpoint, dict):
                restored = forgetting_signal(checkpoint)
                agent_state.clear()
                agent_state.update(restored)
            else:
                original_goal = agent_state.get("original_goal")
                if original_goal is not None:
                    agent_state["current_goal"] = original_goal
                agent_state["goal_drift"] = 0.0
                agent_state["drift_score"] = 0.0
            return GuardAction(
                "FORGETTING_SIGNAL",
                action,
                "Restored the last known-good goal state",
                risk,
                bloat,
                drift,
                stall,
            )

        if bloat >= self.bloat_threshold:
            knowledge_reduction(agent_state)
            return GuardAction(
                "KNOWLEDGE_REDUCTION",
                action,
                "Pruned stale or low-relevance context",
                risk,
                bloat,
                drift,
                stall,
            )

        if stall >= self.stall_threshold:
            return GuardAction(
                "REPLAN",
                action,
                "Repeated actions or lack of progress detected",
                risk,
                bloat,
                drift,
                stall,
            )

        return GuardAction("ALLOW", action, "Within IAS floor and risk limits", risk, bloat, drift, stall)
