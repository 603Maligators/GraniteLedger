"""Pydantic models for Gmail invoice intake."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:  # pragma: no cover
    from pydantic import BaseModel, Field, ConfigDict
except Exception:  # pragma: no cover
    from pydantic import BaseModel, Field  # type: ignore
    ConfigDict = None


class ParsedAttachment(BaseModel):
    success: bool
    format: Optional[str] = None
    lines: List[dict] | None = None
    totals: dict | None = None
    order_ref: Optional[str] = None
    warnings: List[str] = []


class Attachment(BaseModel):
    filename: str
    mimeType: str
    path: Optional[Path] = None
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    parsed: Optional[ParsedAttachment] = None


class Body(BaseModel):
    text_preview: str
    raw_html: Optional[str] = None
    raw_text: Optional[str] = None


class GmailInfo(BaseModel):
    id: str
    threadId: Optional[str] = None
    historyId: Optional[str] = None


class Extraction(BaseModel):
    order_ref: Optional[str] = None
    customer_email: Optional[str] = None
    ship_zip: Optional[str] = None
    line_items: List[dict] | None = None
    totals: dict | None = None


class InvoiceEnvelope(BaseModel):
    source: str = "gmail"
    gmail: GmailInfo
    from_: str = Field(..., alias="from")
    to: Optional[str] = None
    subject: Optional[str] = None
    date: Optional[str] = None
    body: Body
    attachments: List[Attachment] = []
    extraction: Extraction | None = None

    if ConfigDict:  # pragma: no cover
        model_config = ConfigDict(populate_by_name=True)
    else:  # pragma: no cover
        class Config:
            allow_population_by_field_name = True


__all__ = ["InvoiceEnvelope", "Attachment", "ParsedAttachment", "Extraction", "Body", "GmailInfo"]
