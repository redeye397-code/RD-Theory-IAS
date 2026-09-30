# Changelog

## 10.0.0

- Canonicalized project versioning on the V10.0 line; V10 is the only
  supported version, while V1–V9 remain available as archived/reference
  material.
- Added the stable `from rd_guard import RDGuard` import path.
- Kept V9 and V8 import paths available with `DeprecationWarning` notices.
- Migration: replace `from rd_guard_v9 import RDGuard` with
  `from rd_guard import RDGuard`. Existing V9 imports continue to work during
  the compatibility period but are deprecated.
- Added the stable `from rd_vault import GhostVaultProduction` import path for
  the GhostVault secure-enclave attestation API.
- Migration: replace `from rd_theory_v8 import GhostVaultV8_Production` with
  `from rd_vault import GhostVaultProduction`. The archived V8 import path
  continues to work and emits a `DeprecationWarning`.
- Added a canonical action schema (`CanonicalAction`) and the
  `GuardedExecutor` enforcement boundary (`from rd_executor import
  GuardedExecutor`), integrated with the stable `RDGuard` API.
- Added an explicit `SafetyStateMachine` (NORMAL/STABILIZING/BLOCKED/FAULT/
  RECOVERING/COMPROMISED) with a fully documented transition table covering
  trigger/actor, reversibility, required evidence, operator approval,
  restart behavior, repeated-recovery-attempt behavior, and corrupt/missing
  checkpoint handling. See the "State machine" section of README.md.
- `GuardedExecutor` now fails closed for high-risk actions when the audit
  log is unavailable (e.g. simulated disk-full), and the state machine
  guards recovery approvals against replay and clock rollback.
- Fixed `QuorumRate` to enforce the intended bounded 60-second time window
  instead of permitting only a single request for the lifetime of the
  object.
- Expanded CI to run the test suite on Python 3.10, 3.11, and 3.12.
