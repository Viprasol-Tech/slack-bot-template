from __future__ import annotations

import hashlib
import hmac

from slack_bot_template.verify import sign_request, verify_signature

SECRET = "8f742231b10e8888abcd99yyyzzz85a5"
TIMESTAMP = "1531420618"
BODY = "token=xyz&command=%2Fweather&text=94070"


def _reference_signature(secret: str, timestamp: str, body: str) -> str:
    """Independently computed HMAC, mirroring Slack's documented scheme."""
    basestring = f"v0:{timestamp}:{body}".encode()
    digest = hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_sign_request_matches_reference_hmac() -> None:
    assert sign_request(SECRET, TIMESTAMP, BODY) == _reference_signature(SECRET, TIMESTAMP, BODY)


def test_accepts_correctly_signed_request() -> None:
    signature = _reference_signature(SECRET, TIMESTAMP, BODY)
    assert verify_signature(SECRET, TIMESTAMP, BODY, signature, max_skew_seconds=0)


def test_rejects_tampered_body() -> None:
    signature = _reference_signature(SECRET, TIMESTAMP, BODY)
    tampered = BODY + "&injected=1"
    assert not verify_signature(SECRET, TIMESTAMP, tampered, signature, max_skew_seconds=0)


def test_rejects_wrong_secret() -> None:
    signature = _reference_signature(SECRET, TIMESTAMP, BODY)
    assert not verify_signature("other-secret", TIMESTAMP, BODY, signature, max_skew_seconds=0)


def test_rejects_bad_version_prefix() -> None:
    assert not verify_signature(SECRET, TIMESTAMP, BODY, "v9=deadbeef")


def test_rejects_stale_timestamp() -> None:
    signature = sign_request(SECRET, TIMESTAMP, BODY)
    # now is far ahead of TIMESTAMP -> replay rejected.
    assert not verify_signature(
        SECRET, TIMESTAMP, BODY, signature, max_skew_seconds=300, now=2_000_000_000.0
    )


def test_accepts_fresh_timestamp_within_skew() -> None:
    signature = sign_request(SECRET, TIMESTAMP, BODY)
    assert verify_signature(
        SECRET,
        TIMESTAMP,
        BODY,
        signature,
        max_skew_seconds=300,
        now=float(TIMESTAMP) + 10,
    )
