# V11.2.3 LIVE — Security Hardening Release

V11.2.3 hardens the existing fail-closed RD Guard API without changing its
public entry points.

## Security changes

- Action names use one Unicode-aware normalizer and explicit read-only and
  mutating allowlists. Unknown, ambiguous, and destructive actions are blocked
  by default; mutating actions require a healthy audit sink.
- Recovery approvals are HMAC-SHA256 signed, scoped to recovery, expiring, and
  single-use. Configure `RD_RECOVERY_KEY` with at least 32 bytes.
- Checkpoint seals include an HMAC-SHA256 signature and retain `data_hash` for
  compatibility. Configure a separate `RD_CHECKPOINT_KEY` with at least 32
  bytes. Hash-only legacy checkpoints are rejected in strict mode.
- `/check` supports optional `X-API-Key` authentication via `RD_API_KEY`,
  fixed-window client rate limiting (`RD_RATE_LIMIT_PER_MIN`), an 8 KiB body
  limit, and sanitized request-ID-correlated audit/logging.
- CI runs Ruff, mypy, Bandit, pip-audit, tests on Python 3.10–3.12, and Docker
  build/Compose startup checks.
- Removed the unused vulnerable `ecdsa` runtime dependency.

## Configuration

Set `RD_RECOVERY_KEY`, `RD_CHECKPOINT_KEY`, and (in production)
`RD_API_KEY` through a secret manager or deployment environment. Do not commit
their values. The app warns and leaves `/check` unauthenticated when
`RD_API_KEY` is unset. `RD_GUARD_METRICS_HOST` defaults to `127.0.0.1`;
container deployments can set it to `0.0.0.0` for the private Compose network.

## Limitations

RD Guard is not a production-certified security boundary. `run()` callbacks
still execute in-process and are not sandboxed. The default audit sink is
process-local; durable, append-only audit storage and external key management
must be supplied by deployment operators.
