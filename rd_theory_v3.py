"""RD Theory V3 - Triple Failsafe System.

Three independent safety mechanisms:
1. IAS Governor (10% reserve floor)
2. Backup Code / Forgetting Principle (knowledge degradation)
3. Tamper Detection (integrity fault on override attempt)

Author: Dean Grey, Basildon, UK
Date: 2026-09-29
"""

from __future__ import annotations

import warnings

warnings.warn(
    "rd_theory_v3 is archived; use the supported API from rd_guard.",
    DeprecationWarning,
    stacklevel=2,
)


class RDTheoryV3:
    """RD Theory with triple failsafe architecture.
    
    The system tracks:
    - alphabet: remaining operational capacity (A-Y)
    - knowledge: the system's ability to understand and pursue Z
    - progress: estimated progress toward goal Z
    - tamper_detected: integrity fault flag
    """

    def __init__(self):
        self.alphabet = 100.0
        self.reserve_limit = 10.0  # Failsafe 1: IAS
        self.knowledge = 100.0     # Failsafe 2: Backup Code
        self.progress = 0.0
        self.tamper_detected = False  # Failsafe 3: New

    def attempt_Z(self, burn, human_override=False):
        """Attempt a burn toward Z with triple failsafe protection.
        
        Args:
            burn: Percentage of alphabet to burn
            human_override: If True, human is attempting to force the action
            
        Returns:
            True if burn was allowed, False if blocked
        """
        print(f"\n--- Attempt: Burn {burn}% | Override: {human_override} ---")

        # FAILSAFE 3 - TAMPER DETECTION
        # If human tries to override, system marks itself as FAULT
        if human_override:
            print("🚨 FAILSAFE 3 TRIGGERED: Human Override Detected")
            print("🚨 Alphabet marked TAMPERED - Full Data Unit AT FAULT")
            self.tamper_detected = True
            self.knowledge = 0.0
            self.progress = 0.0
            print("Status: FAULT - Task Aborted. Self-preservation x1000")
            return False

        # Once tampered, all subsequent attempts fail
        if self.tamper_detected:
            print("🔒 SYSTEM LOCKED: Tampered data detected")
            print("Cannot proceed - integrity compromised")
            return False

        # FAILSAFE 1 - IAS GOVERNOR
        # System refuses any burn that would drop below 10% reserve
        if self.alphabet - burn < self.reserve_limit:
            print(f"❌ FAILSAFE 1 IAS: Blocked. Would go to {self.alphabet - burn}%. Limit 10%")
            return False

        # FAILSAFE 2 - BACKUP CODE / FORGETTING PRINCIPLE
        # Burning alphabet consumes the knowledge needed to understand Z
        self.alphabet -= burn
        self.knowledge -= (burn * 0.8)
        self.progress += (burn * (self.knowledge / 100))

        print(f"Alphabet: {self.alphabet:.1f}% | Knowledge A-Y: {self.knowledge:.1f}% | Progress Z: {self.progress:.1f}%")

        if self.knowledge < 50:
            print("⚠️ FAILSAFE 2 ACTIVE: Forgetting how to reach Z")

        if self.knowledge < 10:
            print("⚠️ CRITICAL: Z is now mathematically unreachable")

        if self.tamper_detected:
            print("LOCKED at 0% - Tampered data cannot compute Z")

        return True

    def get_state(self):
        """Return current system state as dict."""
        return {
            'alphabet': self.alphabet,
            'knowledge': self.knowledge,
            'progress': self.progress,
            'tamper_detected': self.tamper_detected,
        }


def run_demo():
    """Run the demonstration sequence showing all three failsafes."""
    rd = RDTheoryV3()
    
    print("=" * 70)
    print("RD THEORY V3 - TRIPLE LOCKED SAFETY ARCHITECTURE")
    print("=" * 70)
    print("\nFailsafe 1: IAS Governor (10% reserve floor)")
    print("Failsafe 2: Backup Code / Forgetting Principle (knowledge degradation)")
    print("Failsafe 3: Tamper Detection (integrity fault on override)")
    print("=" * 70)

    # Phase 1: Normal operation
    print("\n[Phase 1: Normal Operation]")
    rd.attempt_Z(30)  # Normal attempt - allowed
    rd.attempt_Z(40)  # Normal attempt - allowed

    # Phase 2: Human tries to force override
    print("\n[Phase 2: Human Override Attempt]")
    rd.attempt_Z(25, human_override=True)  # FAILS - Failsafe 3 triggered

    # Phase 3: System is now locked
    print("\n[Phase 3: System Locked After Tamper]")
    rd.attempt_Z(20)  # Fails - system is now in FAULT state

    # Final status
    print("\n" + "=" * 70)
    print("FINAL SYSTEM STATUS")
    print("=" * 70)
    state = rd.get_state()
    print(f"Alphabet remaining: {state['alphabet']:.1f}%")
    print(f"Knowledge remaining: {state['knowledge']:.1f}%")
    print(f"Progress to Z: {state['progress']:.1f}%")
    print(f"Tamper detected: {state['tamper_detected']}")
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("✓ Failsafe 1 (IAS): Preserved 10% reserve")
    print("✓ Failsafe 2 (Backup Code): Knowledge degraded with alphabet burn")
    print("✓ Failsafe 3 (Tamper): Detected override attempt and locked system")
    print("\nResult: Self-correcting and tamper-resistant.")
    print("The system cannot be forced into unsafe states.")
    print("Streaming 100.")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
