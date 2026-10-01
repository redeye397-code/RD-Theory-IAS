"""HTTP endpoint for exporting RD Guard Prometheus metrics."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from threading import Lock, Thread

from _rd_metrics import DEFAULT_METRICS

_servers = {}
_servers_lock = Lock()


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
    metrics = metrics if metrics is not None else DEFAULT_METRICS
    address = (host, port)

    with _servers_lock:
        existing = _servers.get(address)
        if existing is not None:
            if (
                existing.fileno() >= 0
                and existing.serve_thread.is_alive()
                and existing.metrics is metrics
            ):
                return existing
            _servers.pop(address, None)
            if existing.fileno() >= 0:
                existing.shutdown()
                existing.server_close()

        server = ThreadingHTTPServer(address, _MetricsHandler)
        server.daemon_threads = True
        server.metrics = metrics
        thread = Thread(target=server.serve_forever, daemon=True)
        server.serve_thread = thread
        _servers[address] = server
        thread.start()
        return server


def stop_metrics_server(host, port):
    """Shut down and deregister the cached listener for ``(host, port)``.

    Callers that manage a server's lifecycle directly (for example tests that
    call ``server.shutdown()``/``server.server_close()`` themselves) should use
    this instead so the module-level cache does not retain a stale, closed
    entry indefinitely.
    """
    address = (host, port)
    with _servers_lock:
        existing = _servers.pop(address, None)
        if existing is not None and existing.fileno() >= 0:
            existing.shutdown()
            existing.server_close()


__all__ = ["start_metrics_server", "stop_metrics_server"]
