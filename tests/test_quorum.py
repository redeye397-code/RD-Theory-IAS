import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rd_vault import GhostVaultProduction
import pytest
def test_quorum_rate_limit():
    v = GhostVaultProduction()
    v.quorum.request()
    with pytest.raises(RuntimeError, match="RATE_LIMIT_60S"):
        v.quorum.request()
