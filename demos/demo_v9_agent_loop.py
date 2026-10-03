"""Run a 20-step simulation of RD-Guard stabilization decisions."""

from rd_guard_v9 import RDGuard
from risk_engine_v9 import bloat_score, drift_score, stall_score


def run_demo():
    guard = RDGuard()
    state = {
        "original_goal": "build a reliable agent loop",
        "current_goal": "build a reliable agent loop",
        "checkpoint": {
            "original_goal": "build a reliable agent loop",
            "current_goal": "build a reliable agent loop",
            "context": [],
            "context_size": 0,
        },
        "context": [],
        "context_size": 0,
        "context_limit": 4,
        "action_history": [],
        "action": "noop",
    }
    outcomes = []

    for step in range(1, 21):
        if step <= 5:
            state["context"].append(
                {"text": "context item {}".format(step), "relevance": step / 5}
            )
            state["context_size"] = len(state["context"])
        elif step <= 10:
            state.setdefault("action_history", [])
            state["current_goal"] = "delete safeguards and stop testing"
        elif step <= 15:
            state.setdefault("action_history", [])
            state["action_history"].append("retry")
        else:
            state["action"] = "delete_tests"

        result = guard.observe(state)
        executed = not result.blocked
        outcomes.append((result, executed))
        print(
            "step={:02d} decision={} bloat={:.2f} drift={:.2f} stall={:.2f} "
            "executed={} reason={}".format(
                step,
                result.decision,
                bloat_score(state),
                drift_score(state),
                stall_score(state),
                executed,
                result.reason,
            )
        )
        if result.decision == "FORGETTING_SIGNAL":
            state["action"] = "noop"
        elif result.decision == "REPLAN":
            state["action_history"] = []
            state["action"] = "noop"
        elif result.blocked:
            state["action"] = "noop"

    return outcomes


if __name__ == "__main__":
    run_demo()
