"""Tests for the V11 checkpoint/agent-state schemas.

These cover graceful handling of missing/partial data and the default
values ``Checkpoint``/``AgentState`` fall back to.
"""

from v11.schemas import AgentState, Checkpoint


def test_checkpoint_from_none_returns_safe_defaults():
    checkpoint = Checkpoint.from_dict(None)

    assert checkpoint == Checkpoint(
        original_goal="", current_goal="", context=[], context_size=0
    )


def test_checkpoint_from_empty_dict_returns_safe_defaults():
    checkpoint = Checkpoint.from_dict({})

    assert checkpoint.original_goal == ""
    assert checkpoint.current_goal == ""
    assert checkpoint.context == []
    assert checkpoint.context_size == 0


def test_checkpoint_from_partial_data_fills_in_missing_fields():
    checkpoint = Checkpoint.from_dict({"original_goal": "ship v11"})

    assert checkpoint.original_goal == "ship v11"
    assert checkpoint.current_goal == ""
    assert checkpoint.context == []


def test_checkpoint_context_size_defaults_to_context_length():
    checkpoint = Checkpoint.from_dict({"context": ["a", "b", "c"]})

    assert checkpoint.context_size == 3


def test_checkpoint_handles_non_list_context_gracefully():
    checkpoint = Checkpoint.from_dict({"context": "not-a-list"})

    assert checkpoint.context == ["not-a-list"]


def test_checkpoint_handles_malformed_context_size():
    checkpoint = Checkpoint.from_dict(
        {"context": ["a"], "context_size": "not-an-int"}
    )

    # Falls back to the actual context length rather than crashing.
    assert checkpoint.context_size == 1


def test_agent_state_from_none_returns_safe_defaults():
    state = AgentState.from_dict(None)

    assert state.action is None
    assert state.requested_action is None
    assert state.checkpoint == Checkpoint()
    assert state.context == []
    assert state.context_size == 0
    assert state.context_limit == 0


def test_agent_state_from_partial_data_defaults_nested_checkpoint():
    state = AgentState.from_dict({"action": "noop"})

    assert state.action == "noop"
    assert isinstance(state.checkpoint, Checkpoint)
    assert state.checkpoint.original_goal == ""


def test_agent_state_builds_nested_checkpoint_from_partial_data():
    state = AgentState.from_dict(
        {
            "action": "push",
            "checkpoint": {"original_goal": "ship v11"},
        }
    )

    assert state.checkpoint.original_goal == "ship v11"
    assert state.checkpoint.current_goal == ""


def test_agent_state_handles_malformed_context_limit():
    state = AgentState.from_dict({"context_limit": "not-an-int"})

    assert state.context_limit == 0


def test_agent_state_is_over_context_limit_false_when_no_limit_configured():
    state = AgentState.from_dict({"context_size": 1000})

    assert state.is_over_context_limit is False


def test_agent_state_is_over_context_limit_true_when_exceeded():
    state = AgentState.from_dict({"context_size": 10, "context_limit": 5})

    assert state.is_over_context_limit is True


def test_agent_state_is_over_context_limit_false_when_within_limit():
    state = AgentState.from_dict({"context_size": 3, "context_limit": 5})

    assert state.is_over_context_limit is False
