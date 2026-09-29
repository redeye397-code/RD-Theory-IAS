from rd_theory_v8 import GhostVaultV8_Production
def test_attestation_sig():
    v = GhostVaultV8_Production()
    entry = v.tpm.seal({"msg": "test"})
    assert v.tpm.verify_attestation(entry) == True
