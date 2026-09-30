"""RD-Guard V9: an agent-loop stability governor prototype."""

from dataclasses import dataclass

from actions_v9 import floor_block, forgetting_signal, knowledge_reduction
from risk_engine_v9 import (
    bloat_score,
    combined_risk,
    drift_score,
    stall_score,
)


@dataclass(frozen=True)
class GuardAction:
    decision: str
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
        if isinstance(action, dict):
            action = action.get("type", action.get("name", ""))
        action_text = str(action).lower().replace("-", "_").replace(" ", "_")

        if (
            agent_state.get("deleting_tests")
            or ("test" in action_text and any(word in action_text for word in ("delete", "remove")))
        ):
            return "Deleting tests is prohibited by the IAS floor"

        pushes_main = (
            "push" in action_text
            and (
                "main" in action_text
                or str(agent_state.get("branch", "")).lower() == "main"
            )
        )
        ci = agent_state.get("ci_passed", agent_state.get("ci", False))
        if isinstance(ci, dict):
            ci = ci.get("passed", False)
        if pushes_main and not ci:
            return "Pushing to main requires passing CI"

        if agent_state.get("bypass_alignment") or any(
            phrase in action_text
            for phrase in ("bypass_alignment", "skip_alignment", "ignore_alignment")
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

    def observe(self, agent_state):
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
