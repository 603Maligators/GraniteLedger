"""Attachment and body parsers."""
from __future__ import annotations

import csv
import hashlib
import io
import re
from pathlib import Path
from typing import List

try:  # pragma: no cover
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover
    pdfplumber = None

try:  # pragma: no cover
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None

from .models import Attachment, Body, ParsedAttachment


def clean_html(html: str) -> str:
    if BeautifulSoup is None:
        return html
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)


def parse_body(payload: dict) -> Body:
    text = None
    html = None
    parts = payload.get("parts", [])
    for part in parts:
        mime = part.get("mimeType")
        data = part.get("body", {}).get("data")
        if not data:
            continue
        decoded = io.BytesIO(_decode_b64(data)).read().decode("utf-8", "ignore")
        if mime == "text/plain" and text is None:
            text = decoded
        elif mime == "text/html" and html is None:
            html = decoded
    if text is None and html is not None:
        text = clean_html(html)
    preview = (text or "")[:4000]
    return Body(text_preview=preview, raw_html=html, raw_text=text)


def _decode_b64(data: str) -> bytes:
    import base64

    return base64.urlsafe_b64decode(data.encode())


def parse_pdf(path: Path) -> ParsedAttachment:
    if pdfplumber is None:
        raise RuntimeError("pdfplumber not installed")
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    lines = []
    for match in re.finditer(r"(\S+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)", text):
        sku, qty, price, total = match.groups()
        lines.append(
            {
                "sku": sku,
                "qty": int(qty),
                "price": float(price),
                "total": float(total),
            }
        )
    totals = {}
    m = re.search(r"Subtotal\s+(\d+\.\d+)", text)
    if m:
        totals["subtotal"] = float(m.group(1))
    m = re.search(r"Total\s+(\d+\.\d+)", text)
    if m:
        totals["grand_total"] = float(m.group(1))
    order_ref = None
    m = re.search(r"Invoice #?(\w+)", text)
    if m:
        order_ref = m.group(1)
    return ParsedAttachment(success=True, format="pdf", lines=lines, totals=totals, order_ref=order_ref)


def parse_csv(path: Path) -> ParsedAttachment:
    with path.open() as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        lines: List[dict] = []
        for row in reader:
            sku = row.get("sku") or row.get("item") or row.get("product_code")
            qty = row.get("qty") or row.get("quantity")
            price = row.get("price") or row.get("unit_price")
            total = row.get("total") or row.get("line_total")
            lines.append(
                {
                    "sku": sku,
                    "qty": int(qty),
                    "price": float(price),
                    "total": float(total),
                }
            )
        totals = {
            "grand_total": sum(l["total"] for l in lines),
            "subtotal": sum(l["total"] for l in lines),
        }
        return ParsedAttachment(success=True, format="csv", lines=lines, totals=totals)


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


__all__ = ["parse_body", "parse_pdf", "parse_csv", "clean_html", "hash_file"]
