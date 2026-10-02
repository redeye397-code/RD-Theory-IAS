# Production deployment

RD Guard is a policy and enforcement library, not a certified security boundary.
The sample application and local containers are for evaluation; production
deployments must provide durable audit storage, trusted key custody, and an
operator-controlled recovery process.

## Production checklist

- [ ] Put audit records in a durable, append-only, tamper-evident system. Restrict
  write and read access, alert on failed writes, and test that high-risk actions
  fail closed when the sink is unavailable.
- [ ] Store recovery signing keys in an HSM or TPM-backed service. Never keep
  production keys in the application image, environment variables, or source
  control.
- [ ] Require a documented, independently approved recovery quorum. RD Guard
  accepts recovery approval tokens but does not itself implement distributed
  quorum or HSM integration; supply and validate these controls in the
  deployment integration.
- [ ] Restrict application and metrics network access, run containers as
  non-root where supported, pin and regularly update image versions, and keep
  secrets outside Compose files.
- [ ] Verify backups, restore procedures, alert routing, and incident contacts
  before enabling high-risk actions.

## Metrics configuration

The real-world FastAPI app starts its Prometheus listener during application
startup. Configure it with these environment variables:

| Variable | Default | Description |
|---|---|---|
| `RD_GUARD_METRICS_HOST` | `0.0.0.0` | Address on which the metrics listener binds. |
| `RD_GUARD_METRICS_PORT` | `9090` | TCP port for the `/metrics` endpoint. |
| `RD_GUARD_METRICS_ENABLED` | `true` | Set to `false`, `0`, `no`, or `off` to disable metrics. |

Keep the metrics port on a trusted monitoring network; do not expose it publicly
without an authenticated proxy or equivalent access control. Prometheus histograms
include `rd_guard_observe_duration_seconds`,
`rd_guard_executor_execute_duration_seconds`, and related risk-scoring metrics.

## Recovery operator playbook

1. **FAULT:** Stop or constrain high-risk work and preserve the audit trail,
   process logs, metrics, and the fault evidence. Do not restart repeatedly to
   try to clear the condition: the state machine resumes in `FAULT`.
2. Identify and remediate the root cause (for example, audit-sink failure or a
   hardware fault). Confirm the audit sink and key service are healthy before
   continuing.
3. Have the required recovery quorum validate the incident, checkpoint, and
   recovery plan out of band. Confirm the checkpoint's SHA-256 integrity and
   issue a fresh, single-use approval token; never reuse or bypass an approval.
4. An authorized operator requests **FAULT → RECOVERING** with the checkpoint
   and approval. Monitor transition counters and logs. A failed verification
   returns the machine to `FAULT` and counts toward its bounded retry limit.
5. On successful verification, **RECOVERING → NORMAL** occurs automatically.
   Verify the resulting state and audit records before restoring normal traffic.
   If tampering is confirmed or attempts are exhausted, `COMPROMISED` is terminal;
   use the organization's incident-response procedure rather than attempting
   in-process recovery.

Follow the transition table and approval requirements documented in
[README.md](../README.md#state-machine) and the `SafetyStateMachine` contract.

## Performance tuning

Use Prometheus histogram quantiles as starting service objectives, then measure
under representative production load and set objectives appropriate to the
deployment. Example initial targets for `RDGuard.observe()` are p50 below 5 ms,
p75 below 10 ms, and p99 below 50 ms. These are tuning examples, not measured
or guaranteed performance claims.

```promql
histogram_quantile(0.50, sum by (le) (rate(rd_guard_observe_duration_seconds_bucket[5m])))
histogram_quantile(0.75, sum by (le) (rate(rd_guard_observe_duration_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(rd_guard_observe_duration_seconds_bucket[5m])))
```

Compare observation, validation, and execution histograms separately. Investigate
tail-latency changes alongside traffic, error rates, state transitions, and audit
sink health before changing guard thresholds or weakening enforcement.

## Security hardening and audit retention

- Rotate recovery keys on a documented schedule and immediately after suspected
  exposure. Stage replacements, verify the new key path, revoke the old key, and
  record the rotation in the audit system.
- Archive audit records to access-controlled, immutable storage with retention
  and legal-hold policies appropriate to the organization. Verify integrity and
  retrieval periodically; do not treat container or process-local files as an
  audit archive.
- Use least-privilege service identities and firewall rules. Protect secrets
  through a secret manager and avoid putting credentials in metrics labels,
  logs, images, or Compose configuration.
