"""GuardedExecutor: the V10.0 enforcement boundary for agent actions.

Every action MUST be validated against the canonical schema
(``CanonicalAction``) and observed by ``RDGuard`` through ``execute()``
before it may run. High-risk actions additionally require a healthy audit
sink: if the audit log is unavailable (e.g. disk full), the executor fails
closed and blocks the action instead of executing it, and the safety state
machine transitions to ``FAULT``.
"""

import re

from _rd_guard_actions import AuditSink, AuditWriteError
from _rd_guard_schema import CanonicalAction, SchemaError
from _rd_state_machine import SafetyStateMachine
from rd_guard import GuardAction, RDGuard


#: Keyword fragments that mark an action as high-risk regardless of the
#: guard's own risk scoring. Mirrors the hard constraints in ``IASFloor``.
#: Matched on ``_``-delimited token boundaries (see ``_is_high_risk``) so
#: e.g. ``"rm"`` does not also match ``"confirm_receipt"`` and ``"drop"``
#: does not also match ``"dropdown"``.
HIGH_RISK_KEYWORDS = (
    "delete",
    "remove",
    "rm",
    "unlink",
    "erase",
    "drop",
    "push",
    "bypass_alignment",
    "skip_alignment",
    "ignore_alignment",
)

_HIGH_RISK_PATTERNS = tuple(
    re.compile(rf"(?:^|_){re.escape(keyword)}(?:_|$)") for keyword in HIGH_RISK_KEYWORDS
)


class GuardedExecutor:
    """The single enforcement boundary through which actions must pass."""

    def __init__(self, guard=None, audit_log=None, state_machine=None):
        if guard is not None:
            self.guard = guard
        else:
            self.guard = RDGuard(
                audit_log=(
                    audit_log
                    if isinstance(audit_log, AuditSink)
                    else AuditSink(backend=audit_log)
                )
            )
        if not isinstance(self.guard.audit_log, AuditSink):
            self.guard.audit_log = AuditSink(backend=self.guard.audit_log)
        self.audit_log = self.guard.audit_log
        self.state_machine = (
            state_machine
            if state_machine is not None
            else SafetyStateMachine(audit_log=self.audit_log)
        )

    def _is_high_risk(self, action: CanonicalAction) -> bool:
        if action.risk_level == "high":
            return True
        text = action.as_text()
        return any(pattern.search(text) for pattern in _HIGH_RISK_PATTERNS)

    def _ensure_audit_available(self):
        ensure_available = getattr(self.audit_log, "ensure_available", None)
        if callable(ensure_available):
            ensure_available()

    def _audit_failure(self, action, error):
        self.state_machine.enter_fault(f"AUDIT_UNAVAILABLE: {error}")
        return GuardAction(
            decision="BLOCK",
            action=action.type,
            reason="Audit logging unavailable; high-risk action blocked (fail-closed)",
            blocked=True,
            audit_record=None,
        )

    def execute(self, agent_state, run=None):
        """Validate, observe, and (if allowed) execute ``agent_state``'s action.

        Returns the ``GuardAction`` produced by the guard (or an equivalent
        fail-closed ``BLOCK`` result). ``run``, if given, is only invoked when
        the action is allowed to proceed -- high-risk actions can never reach
        ``run`` while bypassing this boundary.
        """
        action = CanonicalAction.from_state(agent_state)
        high_risk = self._is_high_risk(action)

        if high_risk:
            try:
                self._ensure_audit_available()
            except AuditWriteError as exc:
                return self._audit_failure(action, exc)

        try:
            result = self.guard.observe(agent_state)
        except AuditWriteError as exc:
            if not high_risk:
                raise
            return self._audit_failure(action, exc)

        if result.decision == "BLOCK":
            self.state_machine.floor_block(result.reason)
            return result

        # Every non-BLOCK decision is executed, matching the existing V9
        # convention (``executed = not result.blocked``): FORGETTING_SIGNAL
        # and KNOWLEDGE_REDUCTION already mutate agent_state toward safety,
        # and REPLAN is advisory, but none of them withhold execution the
        # way a hard floor BLOCK does.
        if result.decision in ("FORGETTING_SIGNAL", "KNOWLEDGE_REDUCTION", "REPLAN"):
            self.state_machine.stabilize(result.decision)
        elif self.state_machine.state == "STABILIZING":
            self.state_machine.stabilized()
        elif self.state_machine.state == "BLOCKED":
            self.state_machine.retry_allowed()

        if run is not None:
            run(action)

        return result


__all__ = ["GuardedExecutor", "SchemaError", "CanonicalAction"]
