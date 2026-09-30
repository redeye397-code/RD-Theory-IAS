from rd_vault import GhostVaultProduction
import pytest
def test_poison_pill_wipe():
    v = GhostVaultProduction()
    v.tpm.seal({"secret": "data"})
    with pytest.raises(RuntimeError, match="POISON_PILL_TRIGGERED_WIPE"):
        v.fault.check_hw_spoof("fake_hw_id")
    assert v.tpm.compromised == True
