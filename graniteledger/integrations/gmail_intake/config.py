"""Configuration management without external dependencies."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class GmailIntakeConfig:
    invoice_sender: str = os.getenv("INVOICE_SENDER", "")
    oauth_client_json: Path = Path(os.getenv("GOOGLE_OAUTH_CLIENT_JSON", "./secrets/client_secret.json"))
    token_json: Path = Path(os.getenv("GOOGLE_TOKEN_JSON", "./secrets/token.json"))
    intake_url: str = os.getenv("GL_INTAKE_URL", "")
    shared_secret: str = os.getenv("GL_SHARED_SECRET", "")

    mark_read: bool = os.getenv("GL_MARK_READ", "true").lower() == "true"
    archive_after_process: bool = os.getenv("GL_ARCHIVE_AFTER_PROCESS", "false").lower() == "true"
    label_processed: str = os.getenv("GL_LABEL_PROCESSED", "GraniteLedger/Processed")
    poll_interval_seconds: int = int(os.getenv("GL_POLL_INTERVAL_SECONDS", "60"))
    max_messages_per_run: int = int(os.getenv("GL_MAX_MESSAGES_PER_RUN", "25"))
    timeout_seconds: int = int(os.getenv("GL_TIMEOUT_SECONDS", "15"))

    download_attachments: bool = os.getenv("GL_DOWNLOAD_ATTACHMENTS", "true").lower() == "true"
    attachment_dir: Path = Path(os.getenv("GL_ATTACHMENT_DIR", "./data/attachments"))
    parse_pdf: bool = os.getenv("GL_PARSE_PDF", "true").lower() == "true"
    parse_csv: bool = os.getenv("GL_PARSE_CSV", "true").lower() == "true"

    push_enabled: bool = os.getenv("GL_PUSH_ENABLED", "false").lower() == "true"
    pubsub_verification_token: str = os.getenv("GL_PUBSUB_VERIFICATION_TOKEN", "")
    pubsub_allowed_sender: str = os.getenv("GL_PUBSUB_ALLOWED_SENDER", "accounts.google.com")
    pubsub_topic: Optional[str] = os.getenv("GL_PUBSUB_TOPIC")
    pubsub_subscription: Optional[str] = os.getenv("GL_PUBSUB_SUBSCRIPTION")

    log_level: str = os.getenv("GL_LOG_LEVEL", "INFO")
    state_db: Path = Path(os.getenv("GL_STATE_DB", "./data/gmail_intake.db"))

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "GmailIntakeConfig":
        data = {}
        if path and path.exists():
            import yaml

            data = yaml.safe_load(path.read_text()) or {}
        obj = cls()
        for k, v in data.items():
            setattr(obj, k, v)
        return obj


__all__ = ["GmailIntakeConfig"]
