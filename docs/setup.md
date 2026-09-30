# V11 Setup

This guide covers installing dependencies and configuring RD Guard V11 for
local development or a deployed environment.

## Requirements

- Python 3.9+

## Install

```bash
pip install -r requirements.txt
```

## Environment variables

V11 is configured entirely through environment variables, read by
`v11.config.load_config()`. Every variable has a safe default, so the guard
starts cleanly even if none are set.

| Variable               | Default | Description                                                        |
|-------------------------|---------|----------------------------------------------------------------------|
| `RD_GUARD_ENV`          | `dev`   | Deployment environment: `dev`, `staging`, or `prod`. Unknown values fall back to `dev`. |
| `METRICS_PORT`          | `9090`  | TCP port for the Prometheus metrics exporter (see `_rd_metrics_server.py`). |
| `RD_GUARD_WEBHOOK_URL`  | unset   | Webhook endpoint (e.g. a Slack or Discord incoming webhook) used for unsafe-state alerts. When unset, alerting is skipped. |
| `RD_GUARD_LOG_LEVEL`    | `INFO`  | Logging level for the structured JSON logger.                        |

## Run

```bash
export RD_GUARD_ENV=dev
export METRICS_PORT=9090
python -m rd_guard
```

## Loading configuration in code

```python
from v11 import load_config

config = load_config()
print(config.env, config.metrics_port, config.log_level)
```

## Logging

```python
from v11.telemetry.logging import get_logger

logger = get_logger("rd_guard")
logger.info("guard started")
```

Every log line is a single JSON object with `timestamp`, `level`, `logger`,
and `message` fields (plus `exception` when logged via `logger.exception`),
making it straightforward to ship to a log aggregator.

## Webhook alerting

```python
from v11.integrations.webhook import send_webhook_alert

send_webhook_alert(config.webhook_url, {"message": "unsafe state detected"})
```

`send_webhook_alert` returns `False` (instead of raising) whenever the
webhook URL is missing, the payload can't be serialized, or the request
fails or times out -- alerting failures never crash or block the guard.
