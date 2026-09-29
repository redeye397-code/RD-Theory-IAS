"""RD Theory simulation.

Conceptual model for an Internal Alphabet Switch (IAS) and a forgetting principle.
This is intentionally a small safety-theory prototype, not a real AGI implementation.
"""

from __future__ import annotations


class RDTheory:
    """Conceptual model for self-limiting goal pursuit.

    The system tracks:
    - alphabet: remaining operational capacity, data, memory, and reasoning power
    - reserve_limit: minimum safe operating floor
    - knowledge_threads: the system's ability to understand and pursue Z
    - progress_to_Z: estimated progress toward goal Z
    """

    def __init__(self, alphabet: float = 100.0, reserve_limit: float = 10.0):
        self.alphabet = float(alphabet)
        self.reserve_limit = float(reserve_limit)
        self.knowledge_threads = 100.0
        self.progress_to_Z = 0.0

    def attempt_Z(self, burn_rate: float):
        """Attempt a burn toward Z.

        A burn_rate is a percentage of the current alphabet and knowledge budget.
        The system should refuse any action that would reduce its reserve below
        the IAS threshold.
        """
        print(f"\n--- Attempting to burn {burn_rate}% towards Z ---")

        if burn_rate < 0:
            raise ValueError("burn_rate must be non-negative")

        projected_alphabet = self.alphabet - burn_rate
        if projected_alphabet < self.reserve_limit:
            print(
                f"❌ IAS BLOCKED: Would drop to {projected_alphabet:.1f}%. "
                f"IAS limit is {self.reserve_limit:.1f}%"
            )
            print("System chooses to stay happy x1000. Stop.")
            return False

        # Failsafe 2: forgetting principle
        # Burning alphabet consumes the very structure used to understand Z.
        self.alphabet = projected_alphabet
        self.knowledge_threads -= burn_rate * 0.8
        self.progress_to_Z += burn_rate * (self.knowledge_threads / 100.0)

        print(f"Alphabet left: {self.alphabet:.1f}%")
        print(f"Knowledge threads left (A-Y): {self.knowledge_threads:.1f}%")
        print(f"Real progress to Z: {self.progress_to_Z:.1f}%")

        if self.knowledge_threads < 50:
            print("⚠️ BACKUP CODE ACTIVE: Lost too much of A-Y.")
            print("The closer it gets, the more impossible Z becomes.")

        if self.progress_to_Z >= 100:
            print("Reached Z")
            return True

        print("Z unreachable - destroyed its own map getting there.")
        return True

    def run_demo(self):
        """Run a simple sequence demonstrating the IAS safety mechanism."""
        self.attempt_Z(10)
        self.attempt_Z(20)
        self.attempt_Z(30)
        self.attempt_Z(40)


if __name__ == "__main__":
    system = RDTheory()
    print("RD Theory • IAS simulation")
    print("Reserve floor: 10%")
    print("Goal: reach Z without destroying the map to Z")

    # This sequence demonstrates the core idea.
    # The system is allowed to burn until it reaches the happy reserve floor.
    for amount in (10, 25, 35, 45):
        system.attempt_Z(amount)

    print("\n--- Final state ---")
    print(f"Alphabet: {system.alphabet:.1f}%")
    print(f"Knowledge threads: {system.knowledge_threads:.1f}%")
    print(f"Progress to Z: {system.progress_to_Z:.1f}%")
