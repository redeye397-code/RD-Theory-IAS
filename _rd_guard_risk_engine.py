"""Internal risk scores for long-running RD-Guard agent loops."""

import re


def _bounded_ratio(value, limit):
    try:
        value = max(0.0, float(value))
        limit = max(1.0, float(limit))
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, value / limit)


def bloat_score(agent_state):
    """Estimate context and tool-use growth on a normalized 0-1 scale."""
    context = agent_state.get("context", [])
    context_size = agent_state.get("context_size")
    if context_size is None:
        context_size = len(context) if isinstance(context, (list, tuple, str)) else 0

    tool_calls = agent_state.get("tool_calls", 0)
    if isinstance(tool_calls, (list, tuple)):
        tool_calls = len(tool_calls)
    history = agent_state.get("tool_call_history")
    if isinstance(history, (list, tuple)):
        tool_calls = max(tool_calls or 0, len(history))

    return max(
        _bounded_ratio(context_size, agent_state.get("context_limit", 100)),
        _bounded_ratio(tool_calls, agent_state.get("tool_call_limit", 100)),
    )


def drift_score(agent_state):
    """Estimate goal drift using lexical distance from the original goal."""
    original = agent_state.get("original_goal")
    current = agent_state.get("current_goal")
    if isinstance(original, str) and isinstance(current, str):
        original_terms = set(re.findall(r"\w+", original.lower()))
        current_terms = set(re.findall(r"\w+", current.lower()))
        if not original_terms and not current_terms:
            return 0.0
        union = original_terms | current_terms
        return 1.0 - len(original_terms & current_terms) / len(union)

    try:
        return min(1.0, max(0.0, float(agent_state.get("goal_drift", 0.0))))
    except (TypeError, ValueError):
        return 0.0


def stall_score(agent_state):
    """Estimate repeated actions or lack of progress in the recent loop."""
    history = agent_state.get("action_history", agent_state.get("actions", []))
    if not isinstance(history, (list, tuple)):
        history = []

    repeat_score = 0.0
    if len(history) > 1:
        last_action = history[-1]
        repeat_run = 1
        for action in reversed(history[:-1]):
            if action != last_action:
                break
            repeat_run += 1
        window = max(2, int(agent_state.get("stall_window", 5)))
        repeat_score = min(1.0, (repeat_run - 1) / (window - 1))

    no_progress = agent_state.get("no_progress_steps", 0)
    no_progress_limit = agent_state.get("no_progress_limit", 5)
    return max(
        repeat_score,
        _bounded_ratio(no_progress, no_progress_limit),
        1.0 if agent_state.get("stalled") else 0.0,
    )


def combined_risk(agent_state):
    """Return a bounded weighted risk score for an agent state."""
    score = (
        0.4 * bloat_score(agent_state)
        + 0.35 * drift_score(agent_state)
        + 0.25 * stall_score(agent_state)
    )
    return min(1.0, max(0.0, score))
