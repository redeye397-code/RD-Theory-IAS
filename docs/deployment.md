# Production deployment

RD Guard is a policy and enforcement library, not a certified security boundary.
The sample application and local containers are for evaluation; production
deployments must provide durable audit storage, trusted key custody, and an
operator-controlled recovery process.

## Production checklist

- [ ] Place API ingress, internal service traffic, and the metrics listener in
  explicitly reviewed network zones. Publish only the API listener to clients;
  allow the metrics port only from authenticated/trusted monitoring systems.
- [ ] Put audit records in a durable, append-only, tamper-evident system. Restrict
  write and read access, alert on failed writes, verify retention and restore
  behavior, and test that high-risk actions fail closed when the sink is
  unavailable.
- [ ] Store recovery signing keys in an HSM or TPM-backed service. Never keep
  production keys in the application image, environment variables, or source
  control.
- [ ] Require a documented, independently approved recovery quorum. RD Guard
  accepts recovery approval tokens but does not itself implement distributed
  quorum or HSM integration; supply and validate these controls in the
  deployment integration.
- [ ] Name primary and backup recovery operators, define an incident-response
  deadline and escalation path, and rehearse recovery with a valid checkpoint
  and single-use approval token.
- [ ] Run containers as non-root where supported, pin and regularly update
  image versions, and keep secrets outside Compose files.
- [ ] Verify backups, restore procedures, alert routing, and incident contacts
  before enabling high-risk actions.

## Production readiness checks

Before admitting production traffic, verify these controls in the actual target
environment rather than relying on the development Compose setup:

1. Confirm application dependencies and the `rd_guard/v11/` package files are
   present; dependency/import failures stop startup with an actionable
   `ImportError`.
2. Confirm the API starts and its health check succeeds. `GET /` reports
   application liveness and the metrics status; it does not prove that the
   audit sink, monitoring pipeline, or recovery integration is healthy.
3. Confirm Prometheus can scrape `/metrics` from the trusted monitoring network
   and that the endpoint is not reachable from public ingress. Treat an
   unavailable metrics listener as a readiness failure when observability is a
   production requirement, even though the app intentionally continues to
   serve requests.
4. Exercise audit-sink failure and confirm high-risk actions are blocked.
   Exercise alert delivery, backups/restoration, and the authorized recovery
   process; retain the results with the deployment record.
5. Verify rollback, incident contacts, and operator coverage, then compare
   latency and error observations under representative load before tuning.

## Metrics configuration

The real-world FastAPI app starts its Prometheus listener during application
startup. Metrics are optional: an invalid port or listener bind failure is
logged with configuration/network guidance, the app continues startup, and
`GET /` reports `metrics unavailable`. Missing FastAPI/runtime or `rd_guard`
package dependencies are startup-fatal and report the installation steps.
Configure the listener with these environment variables:

| Variable | Default | Description |
|---|---|---|
| `RD_GUARD_METRICS_HOST` | `0.0.0.0` | Address on which the metrics listener binds. |
| `RD_GUARD_METRICS_PORT` | `9090` | TCP port for the `/metrics` endpoint. |
| `RD_GUARD_METRICS_ENABLED` | `true` | Set to `false`, `0`, `no`, or `off` to disable metrics. |

The default `0.0.0.0` bind listens on all container interfaces. Keep the port
private with service-network policy/firewall rules; in deployments that scrape
locally, bind to a private interface or loopback as appropriate. Do not publish
the metrics port to public ingress. If exposure across trust zones is required,
use an authenticated, access-controlled monitoring path. Prometheus histograms
include `rd_guard_observe_duration_seconds`,
`rd_guard_executor_execute_duration_seconds`, and related risk-scoring metrics;
avoid adding secrets, user identifiers, or other sensitive/high-cardinality
values to metric labels.

## Recovery operator playbook

1. **FAULT:** Stop or constrain high-risk work and preserve the audit trail,
   process logs, metrics, and the fault evidence. Do not restart repeatedly to
   try to clear the condition: the state machine resumes in `FAULT`. Follow the
   incident-response deadline and escalation path defined by the deployment.
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

Recovery requires operators to be reachable for the entire service's supported
operating window. Set response and escalation objectives based on the service's
risk and availability requirements; the library does not define an SLA or
provide an on-call system.

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
