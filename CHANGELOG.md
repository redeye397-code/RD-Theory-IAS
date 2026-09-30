# Changelog

## 10.0.0

- Canonicalized project versioning on the V10.0 line; V10 is the only supported
  version, while V1–V9 remain available as archived/reference material.
- Added the stable `from rd_guard import RDGuard` import path.
- Kept V9 and V8 import paths available with `DeprecationWarning` notices.
- Migration: replace `from rd_guard_v9 import RDGuard` with
  `from rd_guard import RDGuard`. Existing V9 imports continue to work during
  the compatibility period but are deprecated.
- Added the stable `from rd_vault import GhostVaultProduction` import path for
  the GhostVault secure-enclave attestation API.
- Migration: replace `from rd_theory_v8 import GhostVaultV8_Production` with
  `from rd_vault import GhostVaultProduction`. The archived V8 import path
  continues to work and emits a `DeprecationWarning`.
