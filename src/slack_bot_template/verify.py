"""Verify Slack request signatures (HMAC-SHA256).

Slack signs every request to your endpoint. The signature is computed over the
basestring ``"v0:{timestamp}:{body}"`` using your app's *signing secret* as the
HMAC-SHA256 key, then sent as ``v0={hex_digest}`` in the
``X-Slack-Signature`` header alongside ``X-Slack-Request-Timestamp``.

This module implements that scheme exactly. :func:`verify_signature` recomputes
the signature and compares it in constant time, and also rejects stale
timestamps to defend against replay attacks. :func:`sign_request` produces a
matching signature — useful for tests and for any outbound mirroring.

Part of Slack Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import hashlib
import hmac
import time

VERSION = "v0"
"""The signature scheme version prefix Slack currently uses."""

DEFAULT_MAX_SKEW_SECONDS = 60 * 5
"""Reject requests whose timestamp differs from now by more than this."""


def _basestring(timestamp: str, body: str) -> bytes:
    """Build the signed basestring ``v0:{timestamp}:{body}`` as bytes."""
    return f"{VERSION}:{timestamp}:{body}".encode()


def sign_request(signing_secret: str, timestamp: str, body: str) -> str:
    """Compute the Slack ``v0=`` signature for a request.

    Args:
        signing_secret: The app signing secret (HMAC key).
        timestamp: The ``X-Slack-Request-Timestamp`` value (unix seconds).
        body: The exact raw request body.

    Returns:
        The signature string, e.g. ``"v0=a1b2c3..."``.
    """
    digest = hmac.new(
        signing_secret.encode("utf-8"),
        _basestring(timestamp, body),
        hashlib.sha256,
    ).hexdigest()
    return f"{VERSION}={digest}"


def verify_signature(
    signing_secret: str,
    timestamp: str,
    body: str,
    signature: str,
    *,
    max_skew_seconds: int = DEFAULT_MAX_SKEW_SECONDS,
    now: float | None = None,
) -> bool:
    """Verify a Slack request signature in constant time.

    Args:
        signing_secret: The app signing secret (HMAC key).
        timestamp: The ``X-Slack-Request-Timestamp`` header value.
        body: The exact raw request body that was signed.
        signature: The ``X-Slack-Signature`` header value (``"v0=..."``).
        max_skew_seconds: Maximum allowed difference between ``timestamp`` and
            ``now``. Pass a non-positive value to disable the replay check.
        now: Current unix time; defaults to :func:`time.time`. Injectable for
            deterministic tests.

    Returns:
        ``True`` only if the timestamp is fresh and the recomputed signature
        matches the provided one; ``False`` otherwise. Never raises on
        malformed input.
    """
    if not signature.startswith(f"{VERSION}="):
        return False

    if max_skew_seconds > 0:
        try:
            ts = float(timestamp)
        except (TypeError, ValueError):
            return False
        current = time.time() if now is None else now
        if abs(current - ts) > max_skew_seconds:
            return False

    expected = sign_request(signing_secret, timestamp, body)
    return hmac.compare_digest(expected, signature)
