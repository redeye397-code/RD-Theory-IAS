import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rd_vault import GhostVaultProduction, QuorumRate
import pytest
def test_quorum_rate_limit():
    v = GhostVaultProduction()
    v.quorum.request()
    with pytest.raises(RuntimeError, match="RATE_LIMIT_60S"):
        v.quorum.request()


def test_quorum_rate_allows_request_after_window_elapses():
    clock = {"t": 1000.0}
    quorum = QuorumRate(window_seconds=60, clock=lambda: clock["t"])

    quorum.request()

    clock["t"] += 30
    with pytest.raises(RuntimeError, match="RATE_LIMIT_60S"):
        quorum.request()

    clock["t"] += 30.01
    # 60.01s after the first request: the window has elapsed, so a new
    # request is allowed again rather than being blocked for the object's
    # entire lifetime.
    quorum.request()


def test_quorum_rate_blocks_repeatedly_within_the_same_window():
    clock = {"t": 0.0}
    quorum = QuorumRate(window_seconds=60, clock=lambda: clock["t"])

    quorum.request()
    for offset in (1, 10, 59.9):
        clock["t"] = offset
        with pytest.raises(RuntimeError, match="RATE_LIMIT_60S"):
            quorum.request()
