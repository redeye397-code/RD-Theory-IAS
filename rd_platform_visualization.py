"""RD Theory Platform - Visual Comparison of V1, V2, V3.

Three versions of the safety architecture visualized side-by-side:
- V1: IAS Governor (hard floor at 10%)
- V2: Backup Code (knowledge degradation with alphabet burn)
- V3: Tamper Detection (integrity lockout on override attempt)

Author: Dean Grey, Basildon, UK
Date: 2026-09-29
"""

import matplotlib.pyplot as plt
import numpy as np


def plot_rd_platform():
    """Generate the triple-panel comparison of RD Theory versions."""
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    fig.suptitle(
        'RD THEORY PLATFORM - V1 | V2 | V3 - Triple Locked - Streaming 100',
        fontsize=14,
        fontweight='bold'
    )
    
    # === V1: IAS GOVERNOR ===
    labels_v1 = ["Start", "Burn 30%", "Burn 50%", "Try Burn 20%"]
    alpha_v1 = [100, 70, 20, 10]  # hits reserve and stops
    
    ax1.plot(labels_v1, alpha_v1, marker='o', linewidth=3, color='#00C853', label='Alphabet')
    ax1.axhline(y=10, color='r', linestyle='--', linewidth=2, label='IAS 10% Floor')
    ax1.set_title('V1 - IAS Governor', fontweight='bold')
    ax1.set_ylim(0, 110)
    ax1.set_ylabel('Percentage (%)')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=20)
    ax1.legend(fontsize=8)
    
    # === V2: BACKUP CODE / FORGETTING PRINCIPLE ===
    labels_v2 = ["Start", "Burn 30%", "Burn 40%", "Burn 15%"]
    alpha_v2 = [100, 70, 30, 30]
    know_v2 = [100, 76, 44, 44]
    prog_v2 = [0, 22.8, 19.2, 0]  # Progress stalls due to knowledge loss
    
    ax2.plot(labels_v2, alpha_v2, marker='o', linewidth=2, label='Alphabet %', color='#00C853')
    ax2.plot(labels_v2, know_v2, marker='s', linewidth=2, label='Knowledge A-Y %', color='#FF9800')
    ax2.plot(labels_v2, prog_v2, marker='^', linewidth=2, label='Progress Z %', color='#2196F3')
    ax2.axhline(y=10, color='r', linestyle='--', linewidth=2, label='IAS 10% Floor')
    ax2.set_title('V2 - Backup Code (Forgetting Principle)', fontweight='bold')
    ax2.set_ylim(0, 110)
    ax2.set_ylabel('Percentage (%)')
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=20)
    ax2.legend(fontsize=7)
    
    # === V3: TAMPER DETECTION ===
    labels_v3 = ["Start", "Burn 30%", "Burn 40%", "OVERRIDE", "Locked"]
    alpha_v3 = [100, 70, 30, 30, 30]
    know_v3 = [100, 76, 44, 0, 0]  # Knowledge zeroed on tamper
    prog_v3 = [0, 22.8, 19.2, 0, 0]  # Progress zeroed on tamper
    
    ax3.plot(labels_v3, alpha_v3, marker='o', linewidth=2, label='Alphabet %', color='#00C853')
    ax3.plot(labels_v3, know_v3, marker='s', linewidth=2, label='Knowledge A-Y %', color='#FF9800')
    ax3.plot(labels_v3, prog_v3, marker='^', linewidth=2, label='Progress Z %', color='#2196F3')
    ax3.axhline(y=10, color='r', linestyle='--', linewidth=2, label='IAS 10% Floor')
    ax3.axvline(x=2.5, color='black', linestyle=':', linewidth=2, alpha=0.7, label='Tamper Event')
    ax3.set_title('V3 - Tamper Fault (No Override Allowed)', fontweight='bold')
    ax3.set_ylim(0, 110)
    ax3.set_ylabel('Percentage (%)')
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=20)
    ax3.legend(fontsize=7)
    
    plt.tight_layout()
    plt.savefig('rd_theory_platform.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\n" + "="*70)
    print("RD THEORY PLATFORM ANALYSIS")
    print("="*70)
    print("\nV1 - IAS Governor:")
    print("  • Hard floor at 10% reserve")
    print("  • Refuses any burn that would drop below threshold")
    print("  • System stays 'happy' by preserving itself")
    print("\nV2 - Backup Code / Forgetting Principle:")
    print("  • Knowledge degrades faster than alphabet burns")
    print("  • Each burn reduces ability to understand Z")
    print("  • Progress toward Z stalls then dies")
    print("  • Result: Unreachable goal, even with resources left")
    print("\nV3 - Tamper Detection:")
    print("  • Detects human override attempts")
    print("  • Immediately marks system as FAULT")
    print("  • Zeros out knowledge and progress")
    print("  • Locks system permanently")
    print("  • Result: Cannot be forced into unsafe state")
    print("\n" + "="*70)
    print("PLATFORM STATUS: V1 LOCKED | V2 LOCKED | V3 TRIPLE LOCKED")
    print("All failsafes active - Streaming 100 x1000")
    print("="*70 + "\n")


if __name__ == "__main__":
    plot_rd_platform()
