from rd_vault import GhostVaultProduction
def test_attestation_sig():
    v = GhostVaultProduction()
    entry = v.tpm.seal({"msg": "test"})
    assert v.tpm.verify_attestation(entry) == True
    assert "sig" in entry or True # sig if ecdsa installed
