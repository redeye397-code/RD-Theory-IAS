import secrets

import pytest


@pytest.fixture(autouse=True)
def fake_signing_keys(monkeypatch):
    monkeypatch.setenv("RD_RECOVERY_KEY", f"test-{secrets.token_hex(32)}")
    monkeypatch.setenv("RD_CHECKPOINT_KEY", f"test-{secrets.token_hex(32)}")
