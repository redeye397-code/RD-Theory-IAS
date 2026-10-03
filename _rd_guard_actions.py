"""Internal state-reduction and floor-block actions used by RD-Guard."""

from datetime import datetime, timezone


AUDIT_LOG: list[dict] = []


class AuditWriteError(RuntimeError):
    """Raised when an audit record cannot be durably recorded.

    Covers conditions such as audit-disk-full. A full durable, tamper-evident,
    hash-chained audit log with signed event IDs is explicitly out of scope
    for V10.0; this is the minimal seam needed so callers (notably
    ``GuardedExecutor``) can detect audit unavailability and fail closed for
    high-risk actions, per the V10.0 core safety contract.
    """


class AuditSink:
    """Thin wrapper around a list-like audit backend with a failure mode.

    Defaults to appending to the process-local ``AUDIT_LOG`` (the same
    in-memory limitation acknowledged elsewhere in the project), but exposes
    ``mark_unavailable``/``ensure_available`` so tests and callers can
    simulate and detect audit unavailability (e.g. disk full) without
    silently losing high-risk actions.
    """

    def __init__(self, backend=None):
        self._backend = AUDIT_LOG if backend is None else backend
        self._unavailable = False

    def mark_unavailable(self, unavailable=True):
        self._unavailable = unavailable

    def ensure_available(self):
        """Probe the backend with a real write before authorizing risky work."""
        if self._unavailable:
            raise AuditWriteError("audit log unavailable (e.g. disk full)")
        try:
            ensure_backend_available = getattr(self._backend, "ensure_available", None)
            if callable(ensure_backend_available):
                ensure_backend_available()
            self._backend.append({"event": "AUDIT_HEALTH_CHECK"})
        except Exception as exc:
            raise AuditWriteError(f"audit log unavailable: {exc}") from exc

    def append(self, record):
        if self._unavailable:
            raise AuditWriteError("audit log unavailable (e.g. disk full)")
        try:
            self._backend.append(record)
        except Exception as exc:
            raise AuditWriteError(f"audit log unavailable: {exc}") from exc

    def __len__(self):
        return len(self._backend)

    def __iter__(self):
        return iter(self._backend)

    def __getitem__(self, index):
        return self._backend[index]


def knowledge_reduction(agent_state, max_items=None):
    """Prune stale or low-relevance context in place and return the state."""
    context = agent_state.get("context")
    if isinstance(context, (list, tuple)) and context:
        keep_count = max_items
        if keep_count is None:
            keep_count = len(context) // 2
        keep_count = max(0, min(len(context), int(keep_count)))

        ranked = []
        for index, item in enumerate(context):
            if isinstance(item, dict):
                try:
                    relevance = float(item.get("relevance", 0.5))
                except (TypeError, ValueError):
                    relevance = 0.5
                if item.get("stale"):
                    relevance -= 1.0
            else:
                relevance = 0.5
            ranked.append((relevance, index))
        retained = {index for _, index in sorted(ranked, reverse=True)[:keep_count]}
        retained_context = [
            item for index, item in enumerate(context) if index in retained
        ]
        agent_state["context"] = (
            tuple(retained_context) if isinstance(context, tuple) else retained_context
        )
        if "context_size" in agent_state:
            fraction = len(agent_state["context"]) / len(context)
            try:
                agent_state["context_size"] = int(agent_state["context_size"] * fraction)
            except (TypeError, ValueError):
                agent_state["context_size"] = len(agent_state["context"])
    elif isinstance(context, str) and context:
        agent_state["context"] = context[: len(context) // 2]
        if "context_size" in agent_state:
            try:
                agent_state["context_size"] = int(agent_state["context_size"] / 2)
            except (TypeError, ValueError):
                agent_state["context_size"] = len(agent_state["context"])
    return agent_state


def forgetting_signal(checkpoint):
    """Return a restored copy of a known-good checkpoint with drift cleared."""
    if not isinstance(checkpoint, dict):
        raise TypeError("checkpoint must be a dictionary")
    restored = checkpoint.get("state", checkpoint)
    if not isinstance(restored, dict):
        raise TypeError("checkpoint state must be a dictionary")
    restored = dict(restored)
    original_goal = restored.get("original_goal", restored.get("goal"))
    if original_goal is not None:
        restored["original_goal"] = original_goal
        restored["current_goal"] = original_goal
    restored["goal_drift"] = 0.0
    restored["drift_score"] = 0.0
    return restored


def floor_block(reason, audit_log=None):
    """Create a hard BLOCK result and append its record to the audit log."""
    record = {
        "event": "FLOOR_BLOCK",
        "decision": "BLOCK",
        "reason": str(reason),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (AUDIT_LOG if audit_log is None else audit_log).append(record)
    return {
        "decision": "BLOCK",
        "blocked": True,
        "reason": record["reason"],
        "audit_record": record,
    }
