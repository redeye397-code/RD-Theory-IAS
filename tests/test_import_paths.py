import importlib
import warnings

from rd_guard import RDGuard
from rd_executor import GuardedExecutor
from rd_vault import GhostVaultProduction


def test_canonical_rd_guard_import():
    assert RDGuard.__module__ == "rd_guard"


def test_canonical_rd_vault_import():
    assert GhostVaultProduction.__module__ == "_rd_vault_core"


def test_canonical_rd_executor_import():
    assert GuardedExecutor.__module__ == "_rd_guard_executor"


def test_v9_compatibility_import_warns_and_works():
    import rd_guard_v9

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(rd_guard_v9)

    assert rd_guard_v9.RDGuard is RDGuard
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)


def test_v8_reference_import_warns_and_works():
    import rd_theory_v8

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(rd_theory_v8)

    assert rd_theory_v8.GhostVaultV8_Production is GhostVaultProduction
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)


def test_v9_helper_imports_warn_and_work():
    import actions_v9
    import risk_engine_v9

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(actions_v9)
        importlib.reload(risk_engine_v9)

    assert callable(actions_v9.floor_block)
    assert callable(risk_engine_v9.combined_risk)
    assert sum(
        issubclass(item.category, DeprecationWarning) for item in caught
    ) == 2
