"""Thin wrapper around Gmail API."""
from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from .config import GmailIntakeConfig

LOGGER = logging.getLogger(__name__)


class GmailClient:
    """Client for interacting with Gmail REST API via google-api-python-client."""

    def __init__(self, config: GmailIntakeConfig, service=None) -> None:
        scopes = ["https://www.googleapis.com/auth/gmail.modify"]
        if service is None:
            creds = Credentials.from_authorized_user_file(str(config.token_json), scopes)
            service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        self.service = service
        self.user_id = "me"
        self.config = config

    def search_messages(self, max_results: int) -> List[Dict[str, Any]]:
        query = f"from:{self.config.invoice_sender}"
        res = (
            self.service.users()
            .messages()
            .list(userId=self.user_id, q=query, maxResults=max_results)
            .execute()
        )
        return res.get("messages", [])

    def fetch_message(self, msg_id: str) -> Dict[str, Any]:
        return (
            self.service.users()
            .messages()
            .get(userId=self.user_id, id=msg_id, format="full")
            .execute()
        )

    def download_attachment(self, msg_id: str, att_id: str) -> bytes:
        att = (
            self.service.users()
            .messages()
            .attachments()
            .get(userId=self.user_id, messageId=msg_id, id=att_id)
            .execute()
        )
        data = att.get("data", "")
        return base64.urlsafe_b64decode(data.encode())

    def modify_labels(self, msg_id: str, add: List[str] | None = None, remove: List[str] | None = None) -> None:
        body = {"addLabelIds": add or [], "removeLabelIds": remove or []}
        self.service.users().messages().modify(userId=self.user_id, id=msg_id, body=body).execute()

    def get_label_id(self, name: str) -> str:
        labels = self.service.users().labels().list(userId=self.user_id).execute().get("labels", [])
        for lbl in labels:
            if lbl.get("name") == name:
                return lbl["id"]
        # create if missing
        lbl = self.service.users().labels().create(userId=self.user_id, body={"name": name}).execute()
        return lbl["id"]


__all__ = ["GmailClient"]
