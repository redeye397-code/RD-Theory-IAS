# Prometheus alerting example

`prometheus.yml` is a standalone example for running Prometheus on the same
machine/network namespace as the RD Guard metrics listener at `localhost:9090`.
The Docker Compose stack uses `prometheus-compose.yml`, which targets the app
service at `app:9090` on the Compose network. Both load the example rules from
`alerts.yml`.

To use the standalone configuration, install Prometheus, make sure the RD Guard
app is running with metrics enabled, and start Prometheus with:

```sh
prometheus \
  --config.file=examples/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus
```

The rules demonstrate p99 latency, transitions into `FAULT`, the terminal
`COMPROMISED` state, and a spike in blocked actions. Review and tune thresholds
for observed production traffic before paging on them. Alert rules evaluate
inside Prometheus; to deliver notifications, configure an Alertmanager receiver
and routing policy, then connect it with Prometheus's `alerting.alertmanagers`
configuration. Keep Alertmanager credentials in a secret manager, not in this
example configuration.
