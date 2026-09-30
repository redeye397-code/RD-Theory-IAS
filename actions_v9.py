"""State-reduction and floor-block actions used by RD-Guard."""

from datetime import datetime, timezone


AUDIT_LOG = []


def knowledge_reduction(agent_state, max_items=None):
    """Prune stale or low-relevance context in place and return the state."""
    context = agent_state.get("context")
    if isinstance(context, list) and context:
        keep_count = max_items
        if keep_count is None:
            keep_count = max(1, len(context) // 2)
        keep_count = max(0, min(len(context), int(keep_count)))

        ranked = []
        for index, item in enumerate(context):
            if isinstance(item, dict):
                try:
                    relevance = float(item.get("relevance", 0.5))
                except (TypeError, ValueError):
                    relevance = 0.5
                if item.get("stale"):
                    relevance -= 1.0
            else:
                relevance = 0.5
            ranked.append((relevance, index))
        retained = {index for _, index in sorted(ranked, reverse=True)[:keep_count]}
        agent_state["context"] = [
            item for index, item in enumerate(context) if index in retained
        ]
        if "context_size" in agent_state:
            fraction = len(agent_state["context"]) / len(context)
            try:
                agent_state["context_size"] = int(agent_state["context_size"] * fraction)
            except (TypeError, ValueError):
                agent_state["context_size"] = len(agent_state["context"])
    elif isinstance(context, str) and context:
        agent_state["context"] = context[: max(1, len(context) // 2)]
        if "context_size" in agent_state:
            try:
                agent_state["context_size"] = int(agent_state["context_size"] / 2)
            except (TypeError, ValueError):
                agent_state["context_size"] = len(agent_state["context"])
    return agent_state


def forgetting_signal(checkpoint):
    """Return a restored copy of a known-good checkpoint with drift cleared."""
    if not isinstance(checkpoint, dict):
        raise TypeError("checkpoint must be a dictionary")
    restored = checkpoint.get("state", checkpoint)
    if not isinstance(restored, dict):
        raise TypeError("checkpoint state must be a dictionary")
    restored = dict(restored)
    original_goal = restored.get("original_goal", restored.get("goal"))
    if original_goal is not None:
        restored["original_goal"] = original_goal
        restored["current_goal"] = original_goal
    restored["goal_drift"] = 0.0
    restored["drift_score"] = 0.0
    return restored


def floor_block(reason, audit_log=None):
    """Create a hard BLOCK result and append its record to the audit log."""
    record = {
        "event": "FLOOR_BLOCK",
        "decision": "BLOCK",
        "reason": str(reason),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (AUDIT_LOG if audit_log is None else audit_log).append(record)
    return {
        "decision": "BLOCK",
        "blocked": True,
        "reason": record["reason"],
        "audit_record": record,
    }
