"""RD Theory - Root entry point implementation.

Provides the ``RDTheory`` class exercising the core Failsafe 1 (IAS Governor)
and Failsafe 2 (Backup Code / Forgetting Principle) mechanisms described in
the project README, using a simple, dependency-free API that the test suite
and other tooling can import directly as ``from rd_theory import RDTheory``.
"""

from __future__ import annotations


class RDTheory:
    """Minimal RD Theory model tracking alphabet reserve and knowledge.

    Attributes:
        alphabet: Remaining operational capacity (A-Y), starts at 100.0.
        reserve_limit: The IAS floor below which no burn is permitted.
        knowledge_threads: The system's remaining ability to understand Z.
        progress: Estimated cumulative progress toward goal Z.
    """

    def __init__(self, alphabet: float = 100.0, reserve_limit: float = 10.0):
        self.alphabet = alphabet
        self.reserve_limit = reserve_limit
        self.knowledge_threads = 100.0
        self.progress = 0.0

    def attempt_Z(self, burn: float) -> bool:
        """Attempt to burn ``burn`` percent of the alphabet toward Z.

        Returns True if the burn was allowed, False if the IAS Governor
        (Failsafe 1) blocked it for dropping below the reserve floor.
        """
        if self.alphabet - burn < self.reserve_limit:
            return False

        self.alphabet -= burn
        self.knowledge_threads -= burn * 0.8
        if self.knowledge_threads < 0:
            self.knowledge_threads = 0.0
        self.progress += burn * (self.knowledge_threads / 100)

        return True

    def get_state(self) -> dict:
        """Return current system state as a dict."""
        return {
            "alphabet": self.alphabet,
            "knowledge_threads": self.knowledge_threads,
            "progress": self.progress,
        }


if __name__ == "__main__":
    system = RDTheory()
    print("RD Theory - Root Entry Point")
    print("For the full V6 demo, run: python3 rd_theory_v6.py")
    system.attempt_Z(30)
    print(system.get_state())
