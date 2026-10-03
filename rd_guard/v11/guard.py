"""Policy evaluation helpers used by both RDGuard and GuardedExecutor."""

from dataclasses import dataclass

from rd_guard.v11.policy import classify_action


@dataclass(frozen=True)
class PolicyDecision:
    category: str
    reason: str = ""

    @property
    def allowed(self):
        return self.category in {"READ_ONLY", "MUTATING"}

    @property
    def mutating(self):
        return self.category == "MUTATING"


def evaluate_action_policy(agent_state):
    category, reason = classify_action(agent_state)
    return PolicyDecision(category, reason)
