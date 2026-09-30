from rd_vault import GhostVaultProduction
import os, json
def test_tamper_detects():
    audit = "test_tamper.log"
    if os.path.exists(audit): os.remove(audit)
    v = GhostVaultProduction.__new__(GhostVaultProduction)
    from rd_vault import HSM_TPM_SecureEnclave_Production
    v.tpm = HSM_TPM_SecureEnclave_Production(audit_file=audit)
    v.tpm.seal({"a":1})
    v.tpm.seal({"b":2})
    # tamper file
    with open(audit, "r") as f: lines = f.readlines()
    tampered = json.loads(lines[0])
    tampered["data_hash"] = "0"*64
    with open(audit, "w") as f: f.write(json.dumps(tampered)+"\n"); f.writelines(lines[1:])
    v2 = HSM_TPM_SecureEnclave_Production(audit_file=audit)
    assert v2.compromised == True
    os.remove(audit)
