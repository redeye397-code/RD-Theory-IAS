# RD Guard setup

From a local checkout, install the documented runtime/test dependencies and
package with:

```bash
git clone https://github.com/redeye397-code/rd_theory.git
cd rd_theory
python -m pip install -r requirements.txt
python -m pip install -e .
```

The supported RD Guard imports are `RDGuard` from `rd_guard` and
`GuardedExecutor` from `rd_executor`. For the shortest allow/block example, see
the [README quick start](../README.md#try-rd-guard-in-30-seconds).

## Optional webhook notifications

Webhook notifications are opt-in and are not connected to enforcement
automatically. Callers can use the standard-library `WebhookAlerter`; its
default per-instance cooldown is 60 seconds, failed sends count toward that
cooldown, and invalid configuration or failed requests return `False`:

```python
import os

from rd_webhook import WebhookAlerter

alerter = WebhookAlerter()
sent = alerter.send(
    os.environ.get("RD_GUARD_WEBHOOK_URL"), {"event": "action_blocked"}
)
```

Treat webhook URLs as secrets, configure them outside source code, and do not
rely on delivery for enforcement or audit storage.

## Optional Prometheus metrics

The real-world FastAPI app starts the exporter during application startup when
`prometheus-client` is installed. Configure the listener with
`RD_GUARD_METRICS_HOST` and `RD_GUARD_METRICS_PORT`, or disable it with
`RD_GUARD_METRICS_ENABLED=false`. The service continues if the listener cannot
bind; check its startup warning and the
[metrics instructions](../README.md#prometheus-metrics). Without
`prometheus-client`, instrumentation uses no-op metrics and the exporter is
skipped.
