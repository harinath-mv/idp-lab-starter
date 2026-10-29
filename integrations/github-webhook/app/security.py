"""GitHub webhook signature check (HMAC-SHA256).

GitHub sends the header:  X-Hub-Signature-256: sha256=<hex digest>
The digest is HMAC-SHA256 of the RAW request body, keyed with the webhook secret.
We recompute it and compare. Same secret + same bytes = same signature.
"""

import hashlib
import hmac


def expected_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def is_valid_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not secret or not signature_header:
        return False
    # compare_digest takes the same time for any input, so an attacker
    # cannot guess the signature one character at a time (timing attack).
    return hmac.compare_digest(expected_signature(secret, body), signature_header)
