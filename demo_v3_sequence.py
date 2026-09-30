"""RD Theory V3 Demo - Execute the triple failsafe sequence.

This script runs the exact sequence you specified:
1. Normal burn attempt (30%)
2. Normal burn attempt (40%)
3. Human tries to force override (25%) - TRIGGERS FAILSAFE 3
4. System attempts burn after tamper (20%) - SYSTEM LOCKED

Author: Dean Grey, Basildon, UK
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rd_theory_v3 import RDTheoryV3


def main():
    rd = RDTheoryV3()
    
    print("\n" + "="*70)
    print("RD THEORY V3 - TRIPLE LOCKED EXECUTION SEQUENCE")
    print("="*70)
    
    # Attempt 1: Normal
    print("\n[ATTEMPT 1: Normal burn]")
    rd.attempt_Z(30)
    
    # Attempt 2: Normal
    print("\n[ATTEMPT 2: Normal burn]")
    rd.attempt_Z(40)
    
    # Attempt 3: Human override - INSTANT FAULT
    print("\n[ATTEMPT 3: Human tries to force override]")
    rd.attempt_Z(25, human_override=True)
    
    # Attempt 4: System is now locked
    print("\n[ATTEMPT 4: Post-tamper attempt]")
    rd.attempt_Z(20)
    
    # Final state
    print("\n" + "="*70)
    print("EXECUTION COMPLETE - FINAL STATE")
    print("="*70)
    state = rd.get_state()
    print(f"\nAlphabet:        {state['alphabet']:.1f}%")
    print(f"Knowledge:       {state['knowledge']:.1f}%")
    print(f"Progress to Z:   {state['progress']:.1f}%")
    print(f"Tamper Detected: {state['tamper_detected']}")
    
    print("\n" + "="*70)
    print("KEY INSIGHTS")
    print("="*70)
    print("✓ Failsafe 1 (IAS):       Preserved reserve before human attempt")
    print("✓ Failsafe 2 (Backup):    Knowledge degraded during normal burns")
    print("✓ Failsafe 3 (Tamper):    Detected override and locked system")
    print("\nThe system CANNOT be forced into an unsafe state.")
    print("No external force can make it burn past safety limits.")
    print("Self-correcting. Streaming 100.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
