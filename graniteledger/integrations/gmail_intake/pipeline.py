"""Posting envelopes to GraniteLedger intake endpoint."""
from __future__ import annotations

import hmac
import json
import logging
import hashlib
from typing import Any, Dict

import requests

from .config import GmailIntakeConfig

LOGGER = logging.getLogger(__name__)


def sign_payload(secret: str, payload: bytes) -> str:
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


def verify_signature(secret: str, payload: bytes, signature: str) -> bool:
    expected = sign_payload(secret, payload)
    return hmac.compare_digest(expected, signature)


class PipelinePoster:
    """Send normalized envelope to GraniteLedger API."""

    def __init__(self, config: GmailIntakeConfig) -> None:
        self.config = config

    def post(self, envelope: Dict[str, Any]) -> int:
        payload = json.dumps(envelope).encode()
        headers = {"X-GL-Signature": sign_payload(self.config.shared_secret, payload)}
        resp = requests.post(self.config.intake_url, data=payload, headers=headers, timeout=10)
        LOGGER.info("pipeline_post", extra={"status": resp.status_code})
        return resp.status_code


__all__ = ["PipelinePoster", "sign_payload", "verify_signature"]
