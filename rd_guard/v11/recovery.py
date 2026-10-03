"""HMAC-SHA256 recovery approval tokens."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time


class RecoveryTokenError(ValueError):
    """Raised when a recovery token or signing key is invalid."""


def _signing_key(key=None):
    value = os.environ.get("RD_RECOVERY_KEY") if key is None else key
    if isinstance(value, str):
        value = value.encode("utf-8")
    if not isinstance(value, bytes) or len(value) < 32:
        raise RecoveryTokenError("RD_RECOVERY_KEY is missing or too short (minimum 32 bytes)")
    return value


def _encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value):
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)


def issue_recovery_token(operator, key=None, ttl=900, now=None):
    """Issue a single-use, scoped recovery token for an operator."""
    if not isinstance(operator, str) or not operator.strip():
        raise RecoveryTokenError("operator id is required")
    if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or ttl <= 0:
        raise RecoveryTokenError("token ttl must be positive")
    issued_at = time.time() if now is None else now
    if isinstance(issued_at, bool) or not isinstance(issued_at, (int, float)):
        raise RecoveryTokenError("token issue time must be numeric")
    payload = {
        "exp": issued_at + ttl,
        "iat": issued_at,
        "jti": secrets.token_urlsafe(24),
        "operator": operator.strip(),
        "purpose": "recovery",
    }
    encoded = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = hmac.new(_signing_key(key), encoded.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded}.{_encode(signature)}"


def verify_recovery_token(token, now=None, key=None):
    """Validate a token and return its claims without exposing token material."""
    if not isinstance(token, str) or len(token) > 4096 or token.count(".") != 1:
        raise RecoveryTokenError("INVALID_APPROVAL_TOKEN")
    encoded, supplied_signature = token.split(".", 1)
    try:
        signature = _decode(supplied_signature)
        payload = json.loads(_decode(encoded))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise RecoveryTokenError("INVALID_APPROVAL_TOKEN") from None
    expected_signature = hmac.new(
        _signing_key(key), encoded.encode("ascii"), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise RecoveryTokenError("INVALID_APPROVAL_SIGNATURE")
    if not isinstance(payload, dict):
        raise RecoveryTokenError("INVALID_APPROVAL_TOKEN")
    required = ("operator", "jti", "iat", "exp", "purpose")
    if (
        any(field not in payload for field in required)
        or not isinstance(payload["operator"], str)
        or not payload["operator"]
        or not isinstance(payload["jti"], str)
        or not payload["jti"]
        or isinstance(payload["iat"], bool)
        or not isinstance(payload["iat"], (int, float))
        or isinstance(payload["exp"], bool)
        or not isinstance(payload["exp"], (int, float))
        or payload["exp"] <= payload["iat"]
    ):
        raise RecoveryTokenError("INVALID_APPROVAL_TOKEN")
    if payload["purpose"] != "recovery":
        raise RecoveryTokenError("INVALID_APPROVAL_SCOPE")
    timestamp = time.time() if now is None else now
    if timestamp < payload["iat"]:
        raise RecoveryTokenError("APPROVAL_NOT_YET_VALID")
    if timestamp >= payload["exp"]:
        raise RecoveryTokenError("APPROVAL_EXPIRED")
    return payload
