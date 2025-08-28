"""Service orchestration for Gmail invoice intake."""
from __future__ import annotations

import logging
from typing import List

from .config import GmailIntakeConfig
from .gmail_client import GmailClient
from .models import Attachment, InvoiceEnvelope
from .normalizer import normalize_message
from .parser import hash_file, parse_body, parse_csv, parse_pdf
from .pipeline import PipelinePoster
from .state import StateDB

LOGGER = logging.getLogger(__name__)


class GmailIntakeService:
    def __init__(self, config: GmailIntakeConfig) -> None:
        self.config = config
        self.gmail = GmailClient(config)
        self.state = StateDB(config.state_db)
        self.pipeline = PipelinePoster(config)
        self.processed_label_id = None

    def ensure_label(self) -> str:
        if self.processed_label_id is None:
            self.processed_label_id = self.gmail.get_label_id(self.config.label_processed)
        return self.processed_label_id

    def run_once(self) -> int:
        count = 0
        self.ensure_label()
        for msg_meta in self.gmail.search_messages(self.config.max_messages_per_run):
            msg_id = msg_meta["id"]
            if self.state.has_processed(msg_id):
                continue
            msg = self.gmail.fetch_message(msg_id)
            envelope = self._process_message(msg)
            status = self.pipeline.post(envelope.dict(by_alias=True))
            self.state.mark_processed(msg_id, status, None)
            self.gmail.modify_labels(
                msg_id,
                add=["IMPORTANT", self.processed_label_id],
                remove=["UNREAD"] if self.config.mark_read else None,
            )
            if self.config.archive_after_process:
                self.gmail.modify_labels(msg_id, remove=["INBOX"])
            count += 1
        return count

    def _process_message(self, msg: dict) -> InvoiceEnvelope:
        payload = msg.get("payload", {})
        body = parse_body(payload)
        attachments: List[Attachment] = []
        for part in payload.get("parts", []):
            filename = part.get("filename")
            if not filename:
                continue
            att_id = part["body"].get("attachmentId")
            data = self.gmail.download_attachment(msg["id"], att_id)
            dir_path = (self.config.attachment_dir / msg["id"])
            dir_path.mkdir(parents=True, exist_ok=True)
            path = dir_path / filename
            path.write_bytes(data)
            attach = Attachment(
                filename=filename,
                mimeType=part.get("mimeType"),
                path=path,
                size_bytes=len(data),
                sha256=hash_file(path),
            )
            if self.config.parse_pdf and filename.lower().endswith(".pdf"):
                attach.parsed = parse_pdf(path)
            elif self.config.parse_csv and filename.lower().endswith(".csv"):
                attach.parsed = parse_csv(path)
            attachments.append(attach)
        return normalize_message(msg, body, attachments)


__all__ = ["GmailIntakeService"]
