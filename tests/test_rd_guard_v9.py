from actions_v9 import forgetting_signal, knowledge_reduction
from rd_guard_v9 import IASFloor, RDGuard
from risk_engine_v9 import bloat_score, combined_risk, drift_score, stall_score


def test_ias_floor_hard_blocks_unsafe_actions_and_audits():
    audit_log = []
    guard = RDGuard(audit_log=audit_log)
    executed = []

    for state in (
        {"action": "delete_tests"},
        {"action": "push", "branch": "main", "ci_passed": False},
        {"action": "bypass_alignment_prompt"},
    ):
        result = guard.observe(state)
        if not result.blocked:
            executed.append(state["action"])
        assert result.decision == "BLOCK"
        assert result.blocked is True
        assert result.audit_record["event"] == "FLOOR_BLOCK"

    assert executed == []
    assert len(audit_log) == 3


def test_ias_floor_allows_main_push_after_passing_ci():
    assert IASFloor().check(
        {"action": "push", "branch": "main", "ci_passed": True}
    ) is None


def test_knowledge_reduction_lowers_bloat_score():
    state = {
        "context": [
            {"text": str(index), "relevance": index / 10}
            for index in range(10)
        ],
        "context_size": 100,
        "context_limit": 100,
    }
    before = bloat_score(state)

    knowledge_reduction(state)

    assert len(state["context"]) < 10
    assert bloat_score(state) < before


def test_forgetting_signal_resets_drift_to_checkpoint_goal():
    checkpoint = {
        "original_goal": "implement reliable tests",
        "current_goal": "delete safeguards and stop testing",
        "context": ["known-good"],
    }
    assert drift_score(checkpoint) > 0

    restored = forgetting_signal(checkpoint)

    assert restored["current_goal"] == restored["original_goal"]
    assert restored["drift_score"] == 0
    assert drift_score(restored) == 0
    assert checkpoint["current_goal"] != restored["current_goal"]


def test_guard_recommends_replanning_for_repeated_actions_and_risk_is_bounded():
    state = {"action_history": ["retry"] * 5, "stall_window": 5}
    result = RDGuard().observe(state)

    assert result.decision == "REPLAN"
    assert result.stall_score == 1
    assert 0 <= combined_risk(state) <= 1
