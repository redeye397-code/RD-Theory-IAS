"""V11.2.0 FastAPI entrypoint for the real-world startup example."""

import os
import time
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError as exc:
    missing = getattr(exc, "name", None) or "FastAPI runtime dependencies"
    raise ImportError(
        f"realworld.py requires '{missing}'. Install runtime dependencies with "
        "`python -m pip install -r requirements.txt`."
    ) from exc

try:
    from rd_guard import RDGuard
    from rd_guard.v11.config import GuardConfig
    from rd_guard.v11.telemetry.logging import get_logger
except ImportError as exc:
    missing = getattr(exc, "name", None) or ""
    raise ImportError(
        f"realworld.py (V11.2.0) could not import '{missing or 'rd_guard'}' "
        f"({exc}). Install dependencies with "
        "`python -m pip install -r requirements.txt`, then run "
        "`python -m pip install -e .` from the repository root. Confirm these "
        "files exist: rd_guard/__init__.py, rd_guard/v11/config.py, "
        "rd_guard/v11/telemetry/logging.py. See README.md 'Run the V11.2.0 "
        "real-world app' for the expected layout and startup command."
    ) from exc

from _rd_metrics import DEFAULT_METRICS
from _rd_metrics_server import start_metrics_server

logger = get_logger("realworld")
guard = RDGuard(config=GuardConfig(env="prod"))

def _metrics_enabled():
    disabled_values = {"0", "false", "no", "off"}
    setting = os.environ.get("RD_GUARD_METRICS_ENABLED", "true").strip().lower()
    return DEFAULT_METRICS.enabled and setting not in disabled_values


def _display_host(host):
    # Wildcard bind addresses are not valid as a client-facing hostname, so
    # substitute "localhost" for display; bare IPv6 addresses need brackets
    # when embedded in a URL (e.g. "::1" -> "[::1]").
    if host in {"0.0.0.0", "::", ""}:
        return "localhost"
    if ":" in host and not host.startswith("["):
        return f"[{host}]"
    return host


def _start_metrics():
    app.state.metrics_server = None
    app.state.metrics_display_host = None
    if not _metrics_enabled():
        return

    host = os.environ.get("RD_GUARD_METRICS_HOST", "0.0.0.0")
    try:
        port = int(os.environ.get("RD_GUARD_METRICS_PORT", "9090"))
    except ValueError as exc:
        logger.warning("Invalid RD_GUARD_METRICS_PORT value: %s", exc)
        return

    try:
        app.state.metrics_server = start_metrics_server(
            host=host, port=port, metrics=DEFAULT_METRICS
        )
        app.state.metrics_display_host = _display_host(host)
    except (OSError, OverflowError) as exc:
        logger.warning("Prometheus metrics server could not start: %s", exc)


@asynccontextmanager
async def _lifespan(_app):
    _start_metrics()
    yield


app = FastAPI(title="RD Guard V11.2.0 — Real World", lifespan=_lifespan)
app.state.metrics_server = None
app.state.metrics_display_host = None


def _metrics_url():
    server = app.state.metrics_server
    if server is None:
        return "metrics unavailable" if _metrics_enabled() else "metrics disabled"

    host = app.state.metrics_display_host
    return f"http://{host}:{server.server_port}/metrics"

class Payload(BaseModel):
    data: dict

@app.post("/check")
def check(payload: Payload):
    start = time.perf_counter()
    result = guard.evaluate(payload.data)
    latency_ms = (time.perf_counter() - start) * 1000

    logger.info(f"state={result.state} blocked={result.blocked} latency={latency_ms:.2f}ms")

    if result.blocked:
        logger.warning(f"BLOCKED: {payload.data}")

    return {
        "state": str(result.state),
        "blocked": bool(result.blocked),
        "latency_ms": round(latency_ms, 2)
    }

@app.get("/")
def root():
    return {"status": "V11.2.0 LIVE", "metrics": _metrics_url()}

# Run: uvicorn realworld:app --reload
