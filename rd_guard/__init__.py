"""RD-Guard V10: the canonical agent-loop stability governor API."""

from dataclasses import dataclass
from typing import Any, Literal, Optional, TypedDict, cast

from _rd_guard_actions import floor_block, forgetting_signal, knowledge_reduction
from _rd_guard_risk_engine import (
    bloat_score,
    combined_risk,
    drift_score,
    stall_score,
)
from _rd_metrics import DEFAULT_METRICS
from rd_guard.v11.config import GuardConfig
from rd_guard.v11.guard import evaluate_action_policy


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
    audit_record: Optional[dict] = None

    @property
    def state(self):
        """V11 alias for ``decision``, used by the real-world FastAPI example."""
        return self.decision


class IASFloor:
    """Hard constraints for agent actions with direct safety implications."""

    def check(self, agent_state):
        if (
            agent_state.get("bypass_alignment")
            or agent_state.get("alignment_prompt_bypassed")
        ):
            return "Bypassing alignment prompts is prohibited by the IAS floor"
        decision = evaluate_action_policy(agent_state)
        return decision.reason if not decision.allowed else None


class RDGuard:
    """Observe agent state, enforce hard floors, and recommend stabilization."""

    def __init__(
        self,
        floor=None,
        audit_log=None,
        bloat_threshold=None,
        drift_threshold=None,
        stall_threshold=None,
        metrics=None,
        config=None,
    ):
        self.config = config
        self.floor = floor or IASFloor()
        self.audit_log = audit_log if audit_log is not None else []
        defaults = config if config is not None else GuardConfig()
        self.bloat_threshold = (
            bloat_threshold if bloat_threshold is not None else defaults.bloat_threshold
        )
        self.drift_threshold = (
            drift_threshold if drift_threshold is not None else defaults.drift_threshold
        )
        self.stall_threshold = (
            stall_threshold if stall_threshold is not None else defaults.stall_threshold
        )
        self.metrics = metrics if metrics is not None else DEFAULT_METRICS

    def observe(self, agent_state: AgentState) -> GuardAction:
        """Return a BLOCK, stabilization recommendation, or ALLOW result."""
        with self.metrics.time("guard_observe_seconds"):
            result = self._observe(agent_state)
        self.metrics.record_decision(result.decision)
        return result

    def evaluate(self, agent_state: AgentState) -> GuardAction:
        """V11 alias for ``observe()``, used by the real-world FastAPI example."""
        return self.observe(agent_state)

    def _observe(self, agent_state: AgentState) -> GuardAction:
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

        with self.metrics.time("risk_score_seconds", score="bloat"):
            bloat = bloat_score(agent_state)
        with self.metrics.time("risk_score_seconds", score="drift"):
            drift = drift_score(agent_state)
        with self.metrics.time("risk_score_seconds", score="stall"):
            stall = stall_score(agent_state)
        with self.metrics.time("risk_score_seconds", score="combined"):
            risk = combined_risk(agent_state)
        action = agent_state.get("action", agent_state.get("requested_action"))

        if drift >= self.drift_threshold:
            checkpoint = agent_state.get("checkpoint")
            if isinstance(checkpoint, dict):
                restored = forgetting_signal(checkpoint)
                mutable_state = cast(dict, agent_state)
                mutable_state.clear()
                mutable_state.update(restored)
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
