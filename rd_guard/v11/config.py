"""V11 runtime configuration for :class:`rd_guard.RDGuard`.

``GuardConfig`` is a small, dependency-free settings object consumed by
``RDGuard(config=...)``. It mirrors the guard's risk thresholds so a single
object can be constructed per-environment (e.g. ``GuardConfig(env="prod")``)
without requiring callers to pass each threshold individually.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GuardConfig:
    """Environment-scoped settings for ``RDGuard``.

    Attributes:
        env: Deployment environment label (e.g. ``"dev"``, ``"staging"``,
            ``"prod"``). Informational; it does not change guard behavior
            but is useful for logging and telemetry tagging.
        bloat_threshold: Risk score at or above which context is pruned.
        drift_threshold: Risk score at or above which the goal state is
            restored to its last known-good checkpoint.
        stall_threshold: Risk score at or above which a replan is
            recommended.
    """

    env: str = "dev"
    bloat_threshold: float = 0.7
    drift_threshold: float = 0.6
    stall_threshold: float = 0.6
