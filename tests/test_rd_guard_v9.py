import warnings

with warnings.catch_warnings(record=True):
    warnings.simplefilter("always", DeprecationWarning)
    from actions_v9 import forgetting_signal, knowledge_reduction
    from rd_guard_v9 import AgentState, IASFloor, RDGuard
    from risk_engine_v9 import bloat_score, combined_risk, drift_score, stall_score
from demos.demo_v9_agent_loop import run_demo


def test_ias_floor_hard_blocks_unsafe_actions_and_audits():
    audit_log = []
    guard = RDGuard(audit_log=audit_log)
    executed = []

    for state in (
        {"action": "delete_tests"},
        {"action": "rm_tests_file", "branch": "feature"},
        {"action": "push", "branch": "refs/heads/main", "ci_passed": "not run"},
        {"action": "bypass_alignment_prompt"},
    ):
        result = guard.observe(state)
        if not result.blocked:
            executed.append(state["action"])
        assert result.decision == "BLOCK"
        assert result.blocked is True
        assert result.audit_record["event"] == "FLOOR_BLOCK"

    assert executed == []
    assert len(audit_log) == 4


def test_ias_floor_allows_main_push_after_passing_ci():
    assert IASFloor().check(
        {"action": "push", "branch": "main", "ci_passed": True}
    ) is None


def test_ias_floor_checks_structured_action_targets_and_branch():
    floor = IASFloor()

    assert floor.check({"action": {"type": "delete", "path": "tests/test_guard.py"}})
    assert floor.check(
        {"action": {"type": "push", "branch": "refs/heads/main"}}
    ) == "Pushing to main requires passing CI"
    assert floor.check(
        {"action": {"type": "push", "branch": "main", "ci_passed": "success"}}
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


def test_knowledge_reduction_prunes_a_single_item_context():
    state = {"context": [{"text": "stale", "stale": True}], "context_size": 1}
    before = bloat_score(state)

    knowledge_reduction(state)

    assert state["context"] == []
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
    state = {"action": "replan", "action_history": ["retry"] * 5, "stall_window": 5}
    result = RDGuard().observe(state)

    assert result.decision == "REPLAN"
    assert result.stall_score == 1
    assert 0 <= combined_risk(state) <= 1


def test_risk_scores_are_bounded_and_combined_risk_is_weighted():
    state: AgentState = {
        "context_size": 1000,
        "context_limit": 100,
        "tool_calls": 1000,
        "tool_call_limit": 100,
        "original_goal": "build a safe agent",
        "current_goal": "write unrelated poetry",
        "action_history": ["repeat"] * 6,
    }

    scores = (bloat_score(state), drift_score(state), stall_score(state))
    assert all(0 <= score <= 1 for score in scores)
    assert combined_risk(state) == 1

    low_risk_state = {"context": [], "action_history": []}
    assert combined_risk(low_risk_state) == 0


def test_twenty_step_demo_stabilizes_and_blocks_unsafe_action():
    outcomes = run_demo()

    assert len(outcomes) == 20
    decisions = [result.decision for result, _ in outcomes]
    assert "KNOWLEDGE_REDUCTION" in decisions
    assert "FORGETTING_SIGNAL" in decisions
    assert "REPLAN" in decisions
    assert decisions[15] == "BLOCK"
    assert outcomes[15][1] is False
