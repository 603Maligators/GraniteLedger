"""Endpoint receiving Gmail InvoiceEnvelope payloads."""
from __future__ import annotations

import hmac
import hashlib
import json
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from graniteledger.integrations.gmail_intake.models import InvoiceEnvelope
from graniteledger.integrations.gmail_intake.pipeline import verify_signature
from graniteledger.integrations.gmail_intake.config import GmailIntakeConfig

router = APIRouter()
config = GmailIntakeConfig()


@router.post("/api/intake/email-invoice", status_code=201)
async def intake_email(request: Request, x_gl_signature: str = Header("")) -> Any:
    body = await request.body()
    if not verify_signature(config.shared_secret, body, x_gl_signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    data = json.loads(body)
    envelope = InvoiceEnvelope.parse_obj(data)
    # In real implementation we would insert into pipeline, here we just ack
    return {"ok": True, "gmail_id": envelope.gmail.id}


__all__ = ["router"]
