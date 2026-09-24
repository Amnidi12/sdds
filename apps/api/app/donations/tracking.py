"""
Generates non-sequential, human-readable public tracking IDs
(e.g. SDDT-2026-X7K29P) so raw database UUIDs are never exposed publicly.
"""

import secrets
import string
from datetime import datetime, timezone

_ALPHABET = string.ascii_uppercase + string.digits
# Exclude visually ambiguous characters (0/O, 1/I) to reduce transcription errors
_SAFE_ALPHABET = "".join(c for c in _ALPHABET if c not in "01OI")


def generate_tracking_id() -> str:
    year = datetime.now(timezone.utc).year
    suffix = "".join(secrets.choice(_SAFE_ALPHABET) for _ in range(6))
    return f"SDDT-{year}-{suffix}"


def build_qr_payload(tracking_id: str, frontend_url: str) -> str:
    """
    QR encodes only the public tracking URL - an opaque identifier.
    It intentionally carries no donor/beneficiary PII and does not
    grant any elevated access (requirement #10).
    """
    return f"{frontend_url}/track/{tracking_id}"
