"""Normalize Gmail messages into InvoiceEnvelope."""
from __future__ import annotations

from typing import Dict, List

from .models import Attachment, Body, GmailInfo, InvoiceEnvelope


def normalize_message(msg: Dict, body: Body, attachments: List[Attachment]) -> InvoiceEnvelope:
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    gmail_info = GmailInfo(id=msg["id"], threadId=msg.get("threadId"), historyId=msg.get("historyId"))
    return InvoiceEnvelope(
        gmail=gmail_info,
        from_=headers.get("from", ""),
        to=headers.get("to"),
        subject=headers.get("subject"),
        date=headers.get("date"),
        body=body,
        attachments=attachments,
    )


__all__ = ["normalize_message"]
