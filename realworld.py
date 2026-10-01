# realworld.py — V11.2.0 REAL WORLD TEST
from fastapi import FastAPI
from pydantic import BaseModel
import time

try:
    from prometheus_client import start_http_server
except ImportError:
    start_http_server = None

try:
    from rd_guard import RDGuard
    from rd_guard.v11.config import GuardConfig
    from rd_guard.v11.telemetry.logging import get_logger
except ImportError as exc:  # pragma: no cover - exercised via test_realworld_startup.py
    missing = getattr(exc, "name", None) or ""
    if missing == "rd_guard" or missing.startswith("rd_guard."):
        raise ImportError(
            f"realworld.py (V11.2.0) could not import '{missing}' ({exc}). "
            "This usually means the repository was not installed, or the "
            "rd_guard/v11/ submodules are missing. Fix: run "
            "`python -m pip install -e .` from the repository root, and "
            "confirm these files exist: rd_guard/__init__.py, "
            "rd_guard/v11/config.py, rd_guard/v11/telemetry/logging.py. See "
            "README.md 'Run the V11.2.0 real-world app' for the expected "
            "layout and startup command."
        ) from exc
    raise

# 1. Start metrics on :9090 (your Grafana scrapes this)
if start_http_server is not None:
    start_http_server(9090)

logger = get_logger("realworld")
guard = RDGuard(config=GuardConfig(env="prod"))

app = FastAPI(title="RD Guard V11.2.0 — Real World")

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
    metrics_url = "http://localhost:9090/metrics" if start_http_server is not None else "metrics disabled"
    return {"status": "V11.2.0 LIVE", "metrics": metrics_url}

# Run: uvicorn realworld:app --reload
