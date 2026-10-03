"""HMAC-sealed checkpoint helpers."""

import hashlib
import hmac
import os

from _rd_vault_core import canonical


class CheckpointKeyError(ValueError):
    """Raised when a checkpoint signing key is unavailable or too short."""


def _checkpoint_key(key=None):
    value = os.environ.get("RD_CHECKPOINT_KEY") if key is None else key
    if isinstance(value, str):
        value = value.encode("utf-8")
    if not isinstance(value, bytes) or len(value) < 32:
        raise CheckpointKeyError(
            "RD_CHECKPOINT_KEY is missing or too short (minimum 32 bytes)"
        )
    return value


def _serialized(data):
    return canonical(data).encode("utf-8")


def seal_checkpoint(data, key=None):
    """Return checkpoint data, its compatibility hash, and authoritative HMAC."""
    encoded = _serialized(data)
    return {
        "data": data,
        "data_hash": hashlib.sha256(encoded).hexdigest(),
        "signature": hmac.new(_checkpoint_key(key), encoded, hashlib.sha256).hexdigest(),
    }


def checkpoint_signature_valid(checkpoint, key=None):
    """Validate the signed portion of a checkpoint, returning a boolean."""
    if not isinstance(checkpoint, dict) or "data" not in checkpoint:
        return False
    signature = checkpoint.get("signature")
    if not isinstance(signature, str):
        return False
    expected = hmac.new(
        _checkpoint_key(key), _serialized(checkpoint["data"]), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
