"""Tests for the V10.0 canonical action schema (``CanonicalAction``)."""

import pytest

from rd_executor import CanonicalAction, SchemaError


def test_from_state_accepts_bare_string_action():
    action = CanonicalAction.from_state({"action": "noop"})
    assert action.type == "noop"
    assert action.risk_level == "low"


def test_from_state_accepts_structured_action_dict():
    action = CanonicalAction.from_state(
        {"action": {"type": "push", "branch": "main", "ci_passed": True}}
    )
    assert action.type == "push"
    assert action.branch == "main"
    assert action.ci_passed is True


def test_ci_passed_is_coerced_to_a_canonical_bool():
    assert CanonicalAction(type="push", ci_passed="success").ci_passed is True
    assert CanonicalAction(type="push", ci_passed="not run").ci_passed is False
    assert CanonicalAction(type="push", ci_passed={"passed": True}).ci_passed is True
    assert CanonicalAction(type="push", ci_passed=None).ci_passed is False


def test_from_state_accepts_requested_action_field():
    action = CanonicalAction.from_state({"requested_action": "replan"})
    assert action.type == "replan"


def test_from_state_falls_back_to_name_field():
    action = CanonicalAction.from_state({"action": {"name": "delete_tests"}})
    assert action.type == "delete_tests"


def test_from_state_is_idempotent_for_canonical_action():
    action = CanonicalAction(type="noop")
    assert CanonicalAction.from_state(action) is action


def test_missing_type_raises_schema_error():
    with pytest.raises(SchemaError):
        CanonicalAction.from_state({"action": {}})

    with pytest.raises(SchemaError):
        CanonicalAction.from_state({"action": None})


def test_invalid_action_shape_raises_schema_error():
    with pytest.raises(SchemaError):
        CanonicalAction.from_state({"action": 12345})


def test_invalid_risk_level_raises_schema_error():
    with pytest.raises(SchemaError):
        CanonicalAction(type="noop", risk_level="extreme")


def test_empty_type_raises_schema_error():
    with pytest.raises(SchemaError):
        CanonicalAction(type="   ")


def test_as_text_normalizes_and_joins_fields():
    action = CanonicalAction(type="Push-Branch", branch="Refs-Heads-Main")
    text = action.as_text()
    assert "push_branch" in text
    assert "refs_heads_main" in text
