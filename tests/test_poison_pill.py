from rd_theory_v8 import GhostVaultV8_Production
import pytest

def test_poison_pill_wipe():
    v = GhostVaultV8_Production()
    v.tpm.seal({"secret": "data"})
    with pytest.raises(RuntimeError, match="POISON_PILL_TRIGGERED_WIPE"):
        v.fault.check_hw_spoof("fake_hw_id")
    assert v.tpm.compromised is True
