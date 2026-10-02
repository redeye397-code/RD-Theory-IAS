# Changelog

## Unreleased

## 11.2.1 — October 2, 2026

- Deferred the real-world app's Prometheus listener until FastAPI startup,
  made it configurable/disableable, reused an in-process listener, and kept
  port/configuration failures from taking down the app. Added startup,
  metrics, diagnostics, and shell-command coverage and documented Bash and
  PowerShell launch commands.
- Fixed a stale-listener leak: replacing a cached metrics server for an
  address now shuts down and closes the old listener before starting the
  new one, and the real-world app's displayed metrics host is resolved once
  at startup instead of being re-read from the environment per request.
- Fixed the V11.2.0 startup regression: `realworld.py` imported
  `rd_guard.v11.config` and `rd_guard.v11.telemetry.logging`, but `rd_guard`
  was a flat module with no `v11` submodules, so the app failed on import.
  `rd_guard` is now a package (`rd_guard/__init__.py`, preserving the stable
  `from rd_guard import RDGuard` path) with the `rd_guard/v11/config.py`
  (`GuardConfig`) and `rd_guard/v11/telemetry/logging.py` (`get_logger`)
  files the entrypoint expects. Added `RDGuard(config=...)` support and an
  `evaluate()`/`GuardAction.state` alias used by `realworld.py`.
- `realworld.py` now raises an actionable `ImportError` (naming the missing
  module and the fix) instead of failing silently if the `rd_guard` package
  layout is incomplete.

## 11.2.0 — September 30, 2026

- Positioned RD Guard in the README and added local installation and an
  allow/block quick start using the stable V10 API.
- Added setup and architecture documentation, including the limits of the
  enforcement boundary and Prometheus p95 latency guidance.
- Added an optional standard-library webhook notifier with a per-instance
  cooldown; malformed inputs, missing configuration, and failed requests do
  not raise or bypass action enforcement.
- Added malformed canonical-action cases and a 10,000-evaluation schema
  performance regression check with a conservative 10-second CI ceiling.

## 10.0.0

- Set the canonical project version to 10.0.0; V10 is the only supported
  version, while V1–V9 remain available as archived/reference material.
- Added the stable `from rd_guard import RDGuard` import path.
- Kept V9 and V8 import paths available with `DeprecationWarning` notices.
- Kept earlier versioned modules importable for reference with
  `DeprecationWarning` notices.
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
