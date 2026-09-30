import time

from rd_executor import CanonicalAction


def test_canonical_schema_evaluates_ten_thousand_actions():
    start = time.perf_counter()
    for index in range(10_000):
        action = CanonicalAction.from_state(
            {"action": {"type": "read_file", "path": f"docs/{index}.md"}}
        )
        assert action.type == "read_file"
    elapsed = time.perf_counter() - start

    # A deliberately generous ceiling catches hangs or severe regressions while
    # leaving substantial headroom on slower CI runners.
    assert elapsed < 10.0
