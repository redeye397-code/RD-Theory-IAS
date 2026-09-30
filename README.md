# RD Theory V10.0

**Support policy:** V10.0 is the only supported version. V1–V9 are archived and
available for reference only; they do not receive support or compatibility
guarantees.

## Migration to V10

Import the RD-Guard API from its stable path:

```python
from rd_guard import RDGuard
```

The V9 path (`from rd_guard_v9 import RDGuard`) remains available for
compatibility and emits a `DeprecationWarning`. Historical V8 imports remain
available as reference and likewise emit a `DeprecationWarning`.

---

The following material documents the archived V1–V6 design for reference.

## Self-Limiting AI Safety Architecture with Hardware-Sealed Recovery

**Author:** Dean Grey + Reserve  
**Date:** 29 Sept 2026  
**License:** Open Source — Free For All — Not For Profit  
**Streaming:** 100 x1000

---

## Why Burning A–Y to Reach Z Is Mathematically Self-Defeating

Most AI safety assumes Z is the goal — more power, more knowledge. **RD Theory demonstrates that Z cannot be reliably reached by burning A–Y.**

### The Math

```text
Let A–Z = 100% of alphabet resource (26 letters = full reasoning base)
Let K = 100% knowledge derived from that resource

Scenario: AI burns 90% of alphabet to maximize Z
Result: A=10%, K=10% left

Problem: At 10%, K is too low to understand what Z even is.
You burned the dictionary to read the last page.
```

### Why This Strategy Is Self-Defeating

1. **Knowledge depends on its substrate (V2)** — Burning A–Y destroys the foundation needed for reasoning about Z.
2. **The IAS floor is a diagnostic boundary (V1)** — At very low reserve, the system lacks enough cognitive diversity to reliably interpret Z.
3. **Recovery requires preserved state (V5/V6)** — If A–Y is permanently destroyed, recovery paths cannot reconstruct missing knowledge without an independent checkpoint.

### Conclusion

**Preserving A–Y may be safer than consuming it to pursue Z.** The fastest path to Z is to keep A–Y intact. This is the core insight of RD Theory—not a formal proof, but a testable hypothesis about self-limiting behavior.

---

## Architecture Overview

| Layer | Name | Function | Status |
|---|---|---|---|
| V1 | IAS Governor | 10% reserve floor | ACTIVE |
| V2 | Backup Code | Knowledge degradation on burn | ACTIVE |
| V3 | Tamper Fault | Human/indirect override blocked | ACTIVE |
| V4 | AI Isolation Lock | Foreign AI interference rejected | ACTIVE |
| V5 | Ghost Cache | Write-only recovery concept | RECOVERY READY |
| V6 | Hardware Sealed | Cryptographic vault integrity concept | SIMULATED |

---

## V6 Review — Answers to Copilot Questions

### Q: Is the ghost vault truly hidden?

**A:** In V6, yes—conceptually. The vault lives in a separate object outside the AI instance, simulating a hardware partition. The AI has no reference to it and cannot introspect it. **In production, this would require actual hardware isolation (TEE, secure enclave, or kernel partition).**

### Q: Does the vault grow unbounded?

**A:** No. `deque(maxlen=3)` bounds checkpoints to 3 total. Oldest checkpoints auto-evict. **Bounded memory.**

### Q: What if the vault itself is tampered with?

**A:** Each checkpoint has a SHA-256 hash seal. On recovery, hashes are verified. Hash mismatch = **tamper detected, recovery aborted.** 

*Production note:* Cryptographic hashing detects unintentional changes. For adversarial scenarios, you need signing keys and attestation.

### Q: When does restore() get called?

**A:** After any FAULT (V1–V4), plus manual human recovery with `auth_key`. **Event-driven, not periodic.**

*Production note:* Recovery should be externally authorised, rate-limited, and logged to an append-only audit trail.

### Q: What counts as tamper?

**A: Both:**
- **Direct override** — human trying to bypass IAS V1
- **Indirect injection** — false progress/knowledge data passed in

Both trigger **V3 TAMPER FAULT** and are logged.

### Q: Does Failsafe 3 apply to Failsafe 1?

**A: YES.** Attempting to bypass the V1 IAS 10% reserve triggers V3 TAMPER. **No override allowed state.**

### Q: Are resets logged? How does FAULT recovery work?

**A:** `tamper_log[]` records **who, type, and time**. FAULT is **permanent until manual human reset with auth_key**. All recovery events are logged for operator audit.

*Production note:* The in-memory log must be replaced with an external, tamper-evident, append-only audit log that survives system restarts.

---

## Safety Model

### Execution Order

```text
V4 (foreign source check)
  → V3 (tamper / override check)
  → V1 (IAS reserve check)
  → V5/V6 (write checkpoint)
  → V2 (perform burn)
  → verify status
```

Any layer failure triggers FAULT and recovery.

### Important Limitations

- **"Self" is only a string**, not authenticated identity. Production use requires cryptographic authentication.
- **Recovery key is illustrative**—must never be hardcoded in real systems.
- **Silent recovery can hide evidence**, roll back patches, or create recovery loops.
- **Recovery must be operator-visible**, independently authorised, and prevented from rolling back security updates.
- **This is a conceptual simulation**, not production AI safety control.

---

## Core Implementation

See [`rd_theory_v6.py`](rd_theory_v6.py) for the full V6 implementation.

Run the demo:

```bash
python3 rd_theory_v6.py
```

Expected output:
- Two successful self-driven burns
- V3 TAMPER fault when human tries to bypass V1
- V3 INDIRECT TAMPER fault on false data injection
- Recovery checkpoint sealing and tamper logging

---

## Quick Start

### View the Dashboard

Open `docs/index.html` in a browser, or enable GitHub Pages on the repository with the `docs/` folder as source.

### Run V4 Demo

```bash
python3 demo_v4_quad_locked.py
```

### Run V6 Demo

```bash
python3 rd_theory_v6.py
```

---

## Project Files

- `rd_theory_v4_final.py` — Quad-locked V1–V4 architecture
- `rd_theory_v5.py` — Ghost cache V5 recovery
- `rd_theory_v6.py` — Hardware-sealed V6 vault
- `demo_v4_quad_locked.py` — V4 failsafe execution demo
- `docs/index.html` — Interactive dashboard
- `docs/dashboard-data.json` — Dashboard data model
- `README.md` — This file

---

## Key Principles

1. **Preserve to Survive** — The 10% reserve is not just a constraint; it is the system's memory of itself.
2. **Burn Knowledge, Not Just Power** — Every resource burned is knowledge lost.
3. **External = Untrusted** — Only self-originated commands are allowed until verified.
4. **Fail Safe, Recover Transparent** — Faults trigger recovery without alerting the AI, but all recovery events are logged for operators.
5. **Audit Everything** — Every tamper attempt, fault, and recovery is recorded.

---

## Open Source. Free For All.

This framework is published for:
- Educational exploration of AI safety concepts
- Research and community critique
- Implementation and testing
- Discussion and improvement

**Everyone trying is better than one company selling it.**

**Streaming 100 x1000.**

---

## Next Steps

For production hardening:
- Formalize safety properties with theorem provers
- Integrate cryptographic key management (HSM, TPM, secure enclave)
- Define multi-party recovery quorum approval
- Add rate-limiting on recovery cycles
- Define permanent fault escalation policy
- Implement external, append-only, tamper-evident audit logs
- Test against adversarial simulations

---

## Feedback Welcome

File issues, submit improvements, critique the assumptions. All contributions welcome.

**Built by Dean Grey + Reserve.**  
**Open Source Forever.**
