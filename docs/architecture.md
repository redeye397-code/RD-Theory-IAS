# V11 Architecture

V11 layers a production-shaped support module on top of the existing
V10.0 core safety contract (`rd_guard.py`, `rd_executor.py`,
`_rd_guard_schema.py`, `_rd_state_machine.py`, `_rd_vault_core.py`). None of
the V10 public APIs are changed -- V11 is purely additive and lives in the
`v11/` package.

## Design goals

- **Fail closed:** invalid or missing input never crashes the guard; it is
  reduced to a safe default instead.
- **Handle malformed data gracefully:** checkpoint and agent-state payloads
  from upstream systems are frequently partial; `v11/schemas.py` treats
  missing fields as defaults rather than raising.
- **Deployable across environments:** all environment-specific behavior
  (`dev`/`staging`/`prod`, ports, webhook targets, log levels) is
  configured through environment variables, never hard-coded.
- **Observable:** structured JSON logs and (optionally) a webhook alert are
  the two ways an operator finds out something went wrong.
- **Simple:** each module has one responsibility and no required external
  dependencies -- stdlib only.

## Module responsibilities

### `v11/config.py`

Reads `RD_GUARD_ENV`, `METRICS_PORT`, `RD_GUARD_WEBHOOK_URL`, and
`RD_GUARD_LOG_LEVEL` from the environment (or an injected mapping, for
tests) into an immutable `Config` dataclass. Malformed values (an unknown
environment name, a non-numeric port) fall back to defaults instead of
raising, so a bad deployment configuration never prevents startup.

### `v11/schemas.py`

`Checkpoint` and `AgentState` are dataclasses built via `from_dict()`
factory methods that accept `None`, an empty dict, or a partially-populated
dict and always produce a fully-defaulted, well-typed instance. This is the
"reliable data model" V11 is anchored on: callers downstream never need to
guard against missing keys or wrong types.

### `v11/integrations/webhook.py`

`send_webhook_alert(url, payload)` is RD Guard's one real external
integration: a plain HTTP POST of a JSON payload to a webhook URL (Slack
and Discord both accept this shape for incoming webhooks). It is
implemented with the standard library only, and every failure mode --
missing URL, serialization error, network error, timeout, non-2xx response
-- is caught and reported as `False` rather than propagated, so alerting
can never take down the guard it's supposed to be alerting about.

### `v11/telemetry/logging.py`

`get_logger()` returns a standard `logging.Logger` configured with a
`JsonFormatter` that renders every record as one JSON object containing
`timestamp`, `level`, `logger`, `message`, and (when present) `exception`.
This is intentionally a thin wrapper around the standard library so it
composes with existing logging configuration rather than replacing it.

## Data flow (typical usage)

```
raw agent-state payload (possibly partial/malformed)
        │
        ▼
AgentState.from_dict()  ──► safe, typed AgentState
        │
        ▼
RDGuard / GuardedExecutor (V10 core, unchanged)
        │
        ├─► get_logger().info(...)          structured JSON log
        └─► send_webhook_alert(...)         optional alert on unsafe state
```

## Non-goals

- V11 does not replace or modify the V10 `SafetyStateMachine`, the vault,
  or the canonical action schema -- it wraps them with operational
  concerns.
- V11 does not add authentication, a web UI, or a database; those remain
  out of scope for this starter package.
