# RD Theory V8 Production Grade - ECDSA P256 + Wipe + Persistent Audit
# Dean Grey - PENTA LOCKED
import json, time, hashlib, os, threading
from typing import Dict, List
try:
    from ecdsa import SigningKey, VerifyingKey, NIST256p
    HAS_ECDSA = True
except ImportError:
    HAS_ECDSA = False

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

class HSM_TPM_SecureEnclave_Production:
    def __init__(self, audit_file="audit.log.jsonl"):
        self.hw_id = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
        self.compromised = False
        self._audit_file = audit_file
        if HAS_ECDSA:
            self._sk = SigningKey.generate(curve=NIST256p)
            self._vk = self._sk.verifying_key
        else:
            self._sk = self._vk = None
        self._chain: List[Dict] = []
        self._load_and_verify()
        self._heartbeat_thread = None
        self._stop_heartbeat = False

    def _load_and_verify(self):
        if not os.path.exists(self._audit_file):
            return
        try:
            with open(self._audit_file, "r") as f:
                for line in f:
                    entry = json.loads(line)
                    if not self._verify_entry(entry):
                        self._handle_tamper()
                        return
                    self._chain.append(entry)
        except Exception:
            self._handle_tamper()

    def _verify_entry(self, entry):
        # verify chain hash
        if len(self._chain) > 0:
            if entry.get("prev_hash")!= self._chain[-1]["hash"]:
                return False
        # verify ECDSA if present
        if HAS_ECDSA and "sig" in entry:
            try:
                msg = canonical({k: v for k, v in entry.items() if k not in ("sig", "hash")})
                sig_bytes = bytes.fromhex(entry["sig"])
                return self._vk.verify(sig_bytes, msg.encode())
            except Exception:
                return False
        return True

    def _handle_tamper(self):
        self.compromised = True
        tamper_entry = {
            "ts": time.time(),
            "type": "TAMPER_DETECTED",
            "hw_id": self.hw_id,
            "prev_hash": self._chain[-1]["hash"] if self._chain else "0"*64
        }
        tamper_entry["hash"] = hashlib.sha256(canonical(tamper_entry).encode()).hexdigest()
        if HAS_ECDSA:
            tamper_entry["sig"] = self._sk.sign(canonical({k:v for k,v in tamper_entry.items() if k!="hash"}).encode()).hex()
        # append even though tampered
        with open(self._audit_file, "a") as f:
            f.write(canonical(tamper_entry)+"\n")
        self.wipe()

    def wipe(self):
        self.compromised = True
        self._sk = None
        # zero chain in memory
        self._chain.clear()

    def seal(self, data: Dict) -> Dict:
        if self.compromised:
            raise RuntimeError("TPM_COMPROMISED_WIPED")
        entry = {
            "ts": time.time(),
            "type": "SEAL",
            "hw_id": self.hw_id,
            "data_hash": hashlib.sha256(canonical(data).encode()).hexdigest(),
            "prev_hash": self._chain[-1]["hash"] if self._chain else "0"*64,
            "monotonic": time.monotonic()
        }
        entry["hash"] = hashlib.sha256(canonical(entry).encode()).hexdigest()
        if HAS_ECDSA:
            entry["sig"] = self._sk.sign(canonical({k:v for k,v in entry.items() if k not in ("sig","hash")}).encode()).hex()
        # persist append-only
        with open(self._audit_file, "a") as f:
            f.write(canonical(entry)+"\n")
        self._chain.append(entry)
        return entry

    def verify_attestation(self, entry) -> bool:
        return self._verify_entry(entry)

    def verify_chain(self) -> bool:
        if not self._chain:
            return True
        for i in range(1, len(self._chain)):
            if self._chain[i]["prev_hash"]!= self._chain[i-1]["hash"]:
                return False
            if not self._verify_entry(self._chain[i]):
                return False
        return True

class RecoveryQuorumV8Prod:
    def __init__(self, threshold=2):
        self.threshold = threshold
        self._requests: List[float] = []
        self._approvals = 0

    def request(self):
        now = time.time()
        # 60s window + 3 per hour
        self._requests = [t for t in self._requests if now - t < 3600]
        if len([t for t in self._requests if now - t < 60]) >= 1:
            raise RuntimeError("RATE_LIMIT_60S")
        if len(self._requests) >= 3:
            raise RuntimeError("RATE_LIMIT_3_PER_HOUR")
        self._requests.append(now)

    def approve(self):
        self._approvals += 1
        return self._approvals >= self.threshold

class FaultEscalationV8Prod:
    def __init__(self, tpm: HSM_TPM_SecureEnclave_Production):
        self.tpm = tpm

    def check_hw_spoof(self, presented_hw_id):
        if presented_hw_id!= self.tpm.hw_id:
            self.tpm.wipe()
            raise RuntimeError("POISON_PILL_TRIGGERED_WIPE")

class GhostVaultV8_Production:
    def __init__(self):
        self.tpm = HSM_TPM_SecureEnclave_Production()
        self.quorum = RecoveryQuorumV8Prod(threshold=2)
        self.fault = FaultEscalationV8Prod(self.tpm)
        self._heartbeat_times: List[float] = []

    def start_heartbeat(self, interval=0.1):
        def loop():
            while not self.tpm._stop_heartbeat:
                self._heartbeat_times.append(time.monotonic())
                time.sleep(interval)
        self.tpm._stop_heartbeat = False
        self._heartbeat_thread = threading.Thread(target=loop, daemon=True)
        self._heartbeat_thread.start()

    def stop_heartbeat(self):
        self.tpm._stop_heartbeat = True

GhostVaultV8V9 = GhostVaultV8_Production
GhostVaultV8Production = GhostVaultV8_Production
