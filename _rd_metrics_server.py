"""HTTP endpoint for exporting RD Guard Prometheus metrics."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from threading import Thread

from _rd_metrics import DEFAULT_METRICS


class _MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return

        body = self.server.metrics.render()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def start_metrics_server(host=None, port=None, metrics=None):
    """Start a daemon-threaded ``/metrics`` server and return its server object."""
    host = host or os.environ.get("RD_GUARD_METRICS_HOST", "0.0.0.0")
    port = port if port is not None else int(
        os.environ.get("RD_GUARD_METRICS_PORT", "9090")
    )
    server = ThreadingHTTPServer((host, port), _MetricsHandler)
    server.daemon_threads = True
    server.metrics = metrics if metrics is not None else DEFAULT_METRICS
    Thread(target=server.serve_forever, daemon=True).start()
    return server


__all__ = ["start_metrics_server"]
