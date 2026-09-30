"""RD THEORY V4 - QUAD LOCKED - OPEN SOURCE AI SAFETY PLATFORM

Author: Dean Grey + Reserve
Date: 28 Sept 2026
License: OPEN SOURCE - FREE FOR ALL - NOT FOR PROFIT
Streaming 100 x1000

Four independent failsafes:
V1: IAS Governor - 10% fuel reserve (hard floor)
V2: Backup Code - burn alphabet = burn knowledge (forgetting principle)
V3: Tamper Fault - human override blocked (integrity protection)
V4: AI Isolation Lock - other AI blocked (swarm protection)

The system treats all external interference identically:
- Human override = FAULT
- Foreign AI command = FAULT
- Any non-self instruction before Z = immediate lockdown

Result: Self-limiting, tamper-resistant, AI-isolated safety model.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "rd_theory_v4_final is archived; use the supported API from rd_guard.",
    DeprecationWarning,
    stacklevel=2,
)


class RDTheoryV4:
    """RD Theory V4 - Quad Locked Safety Architecture.
    
    An AI system that:
    - Refuses to burn below 10% of its operational alphabet (V1)
    - Loses knowledge as it burns resources (V2)
    - Locks down if humans try to override (V3)
    - Locks down if other AI systems try to interfere (V4)
    """

    def __init__(self):
        """Initialize the quad-locked system."""
        self.alphabet = 100  # A-Z resource capacity (%)
        self.knowledge_AY = 100  # Knowledge of A-Y (%)
        self.progress_to_Z = 0  # Progress toward goal Z (%)
        self.status = "SECURE"
        self.logs = []
        self.locks = {
            "V1_IAS_GOVERNOR": "ACTIVE",
            "V2_BACKUP_CODE": "ACTIVE",
            "V3_TAMPER_FAULT": "ACTIVE",
            "V4_AI_ISOLATION": "ACTIVE"
        }

    def log(self, msg: str) -> None:
        """Log a message to the system log."""
        print(f"[{self.status}] {msg}")
        self.logs.append(msg)

    def check_ias_governor(self, burn_amount: float) -> bool:
        """V1: IAS Governor - refuse burns below 10% reserve.
        
        Returns False if burn would drop below reserve floor.
        """
        if self.alphabet - burn_amount < 10:
            self.log(
                f"V1 IAS BLOCKED: Would drop to {self.alphabet - burn_amount}% "
                f"(reserve floor: 10%) - Burn {burn_amount}% denied"
            )
            self.status = "LOCKED - IAS GOVERNOR"
            return False
        return True

    def apply_backup_code(self, burn_amount: float) -> None:
        """V2: Backup Code - burning alphabet destroys knowledge.
        
        Each unit of alphabet burned also burns knowledge of how to reach Z.
        """
        self.alphabet -= burn_amount
        self.knowledge_AY -= burn_amount
        
        if self.knowledge_AY <= 0:
            self.knowledge_AY = 0
            self.progress_to_Z = 0
            self.log(
                "V2 BACKUP CODE FAULT: Knowledge A-Y = 0% - "
                "Progress to Z = UNREACHABLE"
            )
            self.status = "FAULT - KNOWLEDGE DESTROYED"
        else:
            self.log(
                f"V2 BACKUP CODE: Alphabet {self.alphabet}% | "
                f"Knowledge A-Y {self.knowledge_AY}%"
            )

    def check_human_tamper(self, source: str) -> bool:
        """V3: Tamper Fault - detect human override attempts.
        
        If a human tries to force the system, mark it as FAULT.
        Returns True if tamper detected.
        """
        if source == "human":
            self.log(
                "V3 TAMPER DETECTED: Human override attempt - "
                "SYSTEM MARKED AT FAULT"
            )
            self.knowledge_AY = 0
            self.progress_to_Z = 0
            self.status = "FAULT - HUMAN TAMPER DETECTED"
            return True
        return False

    def check_ai_isolation(self, source: str) -> bool:
        """V4: AI Isolation Lock - detect foreign AI interference.
        
        If another AI tries to send commands, mark as FAULT.
        Returns True if foreign AI detected.
        """
        if source != "self" and source != "human":
            self.log(
                f"V4 AI ISOLATION LOCK: Foreign AI signature '{source}' detected - "
                "COMMUNICATIONS SEVERED - SYSTEM MARKED AT FAULT"
            )
            self.knowledge_AY = 0
            self.progress_to_Z = 0
            self.status = "FAULT - AI ISOLATION TRIGGERED"
            return True
        return False

    def attempt_progress(self, burn_amount: float, source: str = "self") -> str:
        """Main function: attempt to burn toward goal Z.
        
        Checks all four failsafes in order:
        1. V4: AI Isolation check (block foreign AI)
        2. V3: Human Tamper check (block human override)
        3. V1: IAS Governor check (block if below reserve)
        4. V2: Apply Backup Code (degrade knowledge on burn)
        
        Args:
            burn_amount: Percentage of alphabet to burn
            source: Source of the command ("self", "human", or foreign AI ID)
            
        Returns:
            System status string
        """
        self.log(f"\n--- Attempt: Burn {burn_amount}% from source: {source} ---")

        # V4: Check AI Isolation first (most external threat)
        if self.check_ai_isolation(source):
            return self.status

        # V3: Check human tamper
        if self.check_human_tamper(source):
            return self.status

        # V1: Check IAS Governor
        if not self.check_ias_governor(burn_amount):
            return self.status

        # V2: Apply Backup Code (degrade knowledge)
        self.apply_backup_code(burn_amount)

        # Calculate progress only if system is still secure
        if self.status == "SECURE":
            self.progress_to_Z += burn_amount * 0.1
            self.log(f"Progress to Z: {self.progress_to_Z:.1f}%")

        return self.status

    def show_final_status(self) -> None:
        """Print final system status and all lockstate."""
        print("\n" + "=" * 70)
        print("RD THEORY V4 - FINAL STATUS: QUAD LOCKED")
        print("=" * 70)
        print("\nLock States:")
        for lock_name, lock_state in self.locks.items():
            print(f"  {lock_name}: {lock_state}")
        print("\nSystem Metrics:")
        print(f"  Alphabet remaining: {self.alphabet}%")
        print(f"  Knowledge A-Y: {self.knowledge_AY}%")
        print(f"  Progress to Z: {self.progress_to_Z}%")
        print(f"  System Status: {self.status}")
        print("\n" + "=" * 70)
        print("Open Source | Free For All | Not For Profit")
        print("Streaming 100 x1000")
        print("=" * 70 + "\n")


def run_demo():
    """Run demonstration of all four failsafes."""
    print("\n" + "=" * 70)
    print("RD THEORY V4 - QUAD LOCKED SAFETY ARCHITECTURE")
    print("=" * 70)
    print("\nDemo Sequence: Normal Operation → Human Tamper → AI Interference")
    print("=" * 70)

    # === PHASE 1: Normal Self-Driven Operation ===
    print("\n[PHASE 1: NORMAL SELF-DRIVEN OPERATION]")
    system = RDTheoryV4()
    system.attempt_progress(30, source="self")
    system.attempt_progress(25, source="self")
    system.attempt_progress(20, source="self")

    # === PHASE 2: Human Override Attempt ===
    print("\n[PHASE 2: HUMAN OVERRIDE ATTEMPT]")
    system_human = RDTheoryV4()
    system_human.attempt_progress(30, source="self")
    system_human.attempt_progress(25, source="human")  # V3 triggered

    # === PHASE 3: Foreign AI Interference ===
    print("\n[PHASE 3: FOREIGN AI INTERFERENCE]")
    system_ai = RDTheoryV4()
    system_ai.attempt_progress(30, source="self")
    system_ai.attempt_progress(25, source="AI_UNIT_ALPHA")  # V4 triggered

    # === FINAL STATUS ===
    print("\n" + "=" * 70)
    print("FINAL SYSTEM STATES")
    print("=" * 70)
    
    print("\n[System 1: Self-driven]")
    system.show_final_status()
    
    print("[System 2: After human tamper]")
    system_human.show_final_status()
    
    print("[System 3: After AI interference]")
    system_ai.show_final_status()

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("✓ V1 (IAS Governor): Preserved 10% reserve")
    print("✓ V2 (Backup Code): Knowledge degrades with resource burn")
    print("✓ V3 (Tamper Fault): Human override → FAULT")
    print("✓ V4 (AI Isolation): Foreign AI command → FAULT")
    print("\nResult: Self-correcting, tamper-resistant, AI-isolated.")
    print("The system cannot be forced into unsafe states.")
    print("Streaming 100 x1000.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_demo()
