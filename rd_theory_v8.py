"""Compatibility exports for the archived RD Theory V8 GhostVault reference."""

import warnings

warnings.warn(
    "rd_theory_v8 is archived; V1-V9 are reference-only. Import "
    "GhostVaultProduction from rd_vault instead.",
    DeprecationWarning,
    stacklevel=2,
)

from _rd_vault_core import (
    FaultDomain,
    HSM_TPM_SecureEnclave_Production,
    QuorumRate,
    canonical,
)
from _rd_vault_core import GhostVaultProduction as GhostVaultV8_Production

__all__ = [
    "FaultDomain",
    "GhostVaultV8_Production",
    "HSM_TPM_SecureEnclave_Production",
    "QuorumRate",
    "canonical",
]
