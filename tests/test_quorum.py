import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rd_theory_v8 import GhostVaultV8_Production
import pytest
def test_quorum_rate_limit():
    v = GhostVaultV8_Production()
    v.quorum.request()
    with pytest.raises(RuntimeError, match="RATE_LIMIT_60S"):
        v.quorum.request()
