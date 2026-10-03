"""Private implementation for the GhostVault secure-enclave API.

This module backs the canonical `rd_vault` import path. Do not import from
here directly; use `rd_vault` (or the archived, deprecated `rd_theory_v8`
compatibility path) instead.
"""
import hashlib
import json
import os
import threading
import time
from _rd_metrics import DEFAULT_METRICS


def canonical(o):
    return json.dumps(o, sort_keys=True)


class HSM_TPM_SecureEnclave_Production:
    def __init__(self, a="audit.log", audit_file=None, metrics=None):
        self.hw_id = "hw"
        self.compromised = False
        self._a = audit_file if audit_file is not None else a
        self.metrics = metrics if metrics is not None else DEFAULT_METRICS
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
        self.metrics.record_vault_operation("checkpoint_seal", "attempt")
        try:
            with self.metrics.time(
                "vault_operation_seconds", operation="checkpoint_seal"
            ):
                h = hashlib.sha256(canonical(d).encode()).hexdigest()
                e = {"data": d, "data_hash": h, "hw_id": self.hw_id, "ts": time.time(), "sig": "x"}
                persisted = True
                try:
                    with open(self._a, "a") as f:
                        f.write(json.dumps(e) + "\n")
                except OSError:
                    persisted = False
        except Exception:
            self.metrics.record_vault_operation("checkpoint_seal", "failure")
            raise
        self.metrics.record_vault_operation(
            "checkpoint_seal", "success" if persisted else "failure"
        )
        return e

    def verify_attestation(self, e):
        self.metrics.record_vault_operation("attestation_verification", "attempt")
        try:
            with self.metrics.time(
                "vault_operation_seconds", operation="attestation_verification"
            ):
                valid = (
                    hashlib.sha256(canonical(e["data"]).encode()).hexdigest()
                    == e.get("data_hash")
                )
        except Exception:
            self.metrics.record_vault_operation(
                "attestation_verification", "failure"
            )
            raise
        self.metrics.record_vault_operation(
            "attestation_verification", "success" if valid else "failure"
        )
        return valid


class QuorumRate:
    """Rate-limits recovery/quorum requests to one per bounded time window.

    Historically this only allowed a single request for the lifetime of the
    object despite the ``RATE_LIMIT_60S`` name implying a rolling 60-second
    window. It now enforces the intended bounded time-window behavior: a
    second request is rejected only while it falls within ``window_seconds``
    of the previous one; once the window elapses, requests are allowed again.
    """

    def __init__(self, window_seconds=60, clock=time.time):
        self.window_seconds = window_seconds
        self._clock = clock
        self._last_request_time = None

    def request(self):
        now = self._clock()
        if (
            self._last_request_time is not None
            and (now - self._last_request_time) < self.window_seconds
        ):
            raise RuntimeError("RATE_LIMIT_60S")
        self._last_request_time = now


class FaultDomain:
    def __init__(self, p):
        self.parent = p

    def check_hw_spoof(self, f):
        self.parent.tpm.compromised = True
        raise RuntimeError("POISON_PILL_TRIGGERED_WIPE")


class GhostVaultProduction:
    def __init__(self, a="audit.log", metrics=None):
        self.metrics = metrics if metrics is not None else DEFAULT_METRICS
        self.tpm = HSM_TPM_SecureEnclave_Production(a, metrics=self.metrics)
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

        threading.Thread(target=L, daemon=True).start()

    def stop_heartbeat(self):
        self._run = False
