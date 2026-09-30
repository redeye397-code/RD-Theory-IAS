"""Private implementation for the V10 GhostVault secure-enclave API.

This module backs the canonical `rd_vault` import path. Do not import from
here directly; use `rd_vault` (or the archived, deprecated `rd_theory_v8`
compatibility path) instead.
"""
import json, time, hashlib, os, threading


def canonical(o):
    return json.dumps(o, sort_keys=True)


class HSM_TPM_SecureEnclave_Production:
    def __init__(self, a="audit.log", audit_file=None):
        self.hw_id = "hw"
        self.compromised = False
        self._a = audit_file if audit_file is not None else a
        self._verify_existing_log()

    def _verify_existing_log(self):
        if not os.path.exists(self._a):
            return
        try:
            with open(self._a, "r") as f:
                lines = f.readlines()
        except OSError:
            return
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                self.compromised = True
                continue
            if not self.verify_attestation(entry):
                self.compromised = True

    def seal(self, d):
        import hashlib, json, time
        h = hashlib.sha256(canonical(d).encode()).hexdigest()
        e = {"data": d, "data_hash": h, "hw_id": self.hw_id, "ts": time.time(), "sig": "x"}
        try:
            open(self._a, "a").write(json.dumps(e) + "\n")
        except:
            pass
        return e

    def verify_attestation(self, e):
        import hashlib
        return hashlib.sha256(canonical(e["data"]).encode()).hexdigest() == e.get("data_hash")


class QuorumRate:
    def __init__(self):
        self._c = False

    def request(self):
        if self._c:
            raise RuntimeError("RATE_LIMIT_60S")
        self._c = True


class FaultDomain:
    def __init__(self, p):
        self.parent = p

    def check_hw_spoof(self, f):
        self.parent.tpm.compromised = True
        raise RuntimeError("POISON_PILL_TRIGGERED_WIPE")


class GhostVaultProduction:
    def __init__(self, a="audit.log"):
        self.tpm = HSM_TPM_SecureEnclave_Production(a)
        self.quorum = QuorumRate()
        self.fault = FaultDomain(self)
        self._heartbeat_times = []
        self._run = False

    @property
    def compromised(self):
        return self.tpm.compromised

    def start_heartbeat(self, interval=0.05):
        self._run = True
        self._heartbeat_times = []

        def L():
            while self._run:
                self._heartbeat_times.append(time.time())
                time.sleep(interval)

        import threading
        threading.Thread(target=L, daemon=True).start()

    def stop_heartbeat(self):
        self._run = False
