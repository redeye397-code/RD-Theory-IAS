# RD Guard architecture

## Action enforcement

`GuardedExecutor` is the public action execution path. It normalizes inputs
through `CanonicalAction`, identifies high-risk actions, checks audit
availability when required, and passes valid state to `RDGuard`. The guard
applies the IAS safety floor and risk evaluation. Hard-blocked actions are not
sent to the optional execution callback. Audit failures for high-risk actions
fail closed and move the state machine to `FAULT`.

The explicit `SafetyStateMachine` tracks `NORMAL`, `STABILIZING`, `BLOCKED`,
`FAULT`, `RECOVERING`, and terminal `COMPROMISED` states. See the README state
machine transition table for the documented transitions and recovery rules.

This implementation is a Python enforcement component, not a
production-certified security boundary. Production deployments still require
appropriate process isolation, access control, durable audit storage, and
independent review.

The real-world FastAPI example binds its API and optional metrics exporter on
separate listeners. Operators must define network policy for each boundary;
the metrics endpoint is intended for trusted monitoring systems, not public
clients. Its `GET /` response is an application liveness signal only and does
not attest to audit-sink, metrics-scrape, or recovery readiness. High-risk
actions still fail closed when required audit checks fail.

## Optional integrations and observability

`WebhookAlerter` sends caller-selected JSON notifications over HTTP(S). It is
separate from the execution path, rate-limits each instance with a default
60-second cooldown, and returns `False` on invalid input or delivery failure.
Callers must decide which events to notify; webhook delivery is not guaranteed
and does not replace the audit sink.

Prometheus instrumentation is optional. When enabled, latency histograms cover
guard observation, risk scoring, executor validation/execution, and vault
operations. Use `histogram_quantile(0.95, sum(rate(<histogram>_bucket[5m])) by
(le))` to estimate a rolling p95 for a histogram, such as
`rd_guard_executor_execute_duration_seconds`. Compare measured components
before optimizing; the CI schema benchmark uses a conservative 10-second
ceiling for 10,000 evaluations rather than a machine-sensitive microbenchmark.
