"""Optional Prometheus instrumentation for RD Guard."""

from contextlib import contextmanager
import importlib
import time


_AUTO_CLIENT = object()
_STATES = ("NORMAL", "STABILIZING", "BLOCKED", "FAULT", "RECOVERING", "COMPROMISED")


class PrometheusMetrics:
    """Small metrics facade that degrades to no-ops without prometheus-client."""

    def __init__(self, registry=None, prometheus_client=_AUTO_CLIENT):
        if prometheus_client is _AUTO_CLIENT:
            try:
                prometheus_client = importlib.import_module("prometheus_client")
            except ImportError:
                prometheus_client = None

        self.enabled = prometheus_client is not None
        self._client = prometheus_client
        self._metrics = {}
        self.registry = None
        if not self.enabled:
            return

        registry = (
            registry
            if registry is not None
            else prometheus_client.CollectorRegistry()
        )
        self.registry = registry
        self._metrics = {
            "actions": prometheus_client.Counter(
                "rd_guard_action_decisions",
                "Guard decisions by action type.",
                ("decision",),
                registry=registry,
            ),
            "transitions": prometheus_client.Counter(
                "rd_guard_state_transitions",
                "Safety state machine transitions.",
                ("from_state", "to_state", "event"),
                registry=registry,
            ),
            "state": prometheus_client.Gauge(
                "rd_guard_safety_state",
                "One-hot gauge for the current safety state.",
                ("state",),
                registry=registry,
            ),
            "vault_operations": prometheus_client.Counter(
                "rd_guard_vault_operations",
                "Vault operations by operation and outcome.",
                ("operation", "outcome"),
                registry=registry,
            ),
            "guard_observe_seconds": prometheus_client.Histogram(
                "rd_guard_observe_duration_seconds",
                "RD Guard observation cycle duration.",
                registry=registry,
            ),
            "risk_score_seconds": prometheus_client.Histogram(
                "rd_guard_risk_score_duration_seconds",
                "Risk score calculation duration.",
                ("score",),
                registry=registry,
            ),
            "executor_validation_seconds": prometheus_client.Histogram(
                "rd_guard_executor_validation_duration_seconds",
                "GuardedExecutor action validation duration.",
                registry=registry,
            ),
            "executor_execution_seconds": prometheus_client.Histogram(
                "rd_guard_executor_execution_duration_seconds",
                "GuardedExecutor action callback duration.",
                registry=registry,
            ),
            "executor_execute_seconds": prometheus_client.Histogram(
                "rd_guard_executor_execute_duration_seconds",
                "Complete GuardedExecutor execute call duration.",
                registry=registry,
            ),
            "vault_operation_seconds": prometheus_client.Histogram(
                "rd_guard_vault_operation_duration_seconds",
                "Vault operation duration.",
                ("operation",),
                registry=registry,
            ),
        }

    def record_decision(self, decision):
        if self.enabled:
            self._metrics["actions"].labels(decision=decision).inc()

    def record_transition(self, from_state, to_state, event):
        if self.enabled:
            self._metrics["transitions"].labels(
                from_state=from_state, to_state=to_state, event=event
            ).inc()
            for state in _STATES:
                self._metrics["state"].labels(state=state).set(state == to_state)

    def set_state(self, state):
        if self.enabled:
            for known_state in _STATES:
                self._metrics["state"].labels(state=known_state).set(
                    known_state == state
                )

    def record_vault_operation(self, operation, outcome):
        if self.enabled:
            self._metrics["vault_operations"].labels(
                operation=operation, outcome=outcome
            ).inc()

    @contextmanager
    def time(self, metric, **labels):
        started = time.perf_counter()
        try:
            yield
        finally:
            if self.enabled:
                histogram = self._metrics[metric]
                if labels:
                    histogram = histogram.labels(**labels)
                histogram.observe(time.perf_counter() - started)

    def render(self):
        if not self.enabled:
            return b""
        return self._client.generate_latest(self.registry)


DEFAULT_METRICS = PrometheusMetrics()
