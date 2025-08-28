"""FastAPI router handling Gmail push notifications."""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException

from .config import GmailIntakeConfig
from .service import GmailIntakeService

LOGGER = logging.getLogger(__name__)
router = APIRouter()


def get_service() -> GmailIntakeService:
    config = GmailIntakeConfig()
    return GmailIntakeService(config)


@router.post("/gmail/push", status_code=204)
async def gmail_push(
    background: BackgroundTasks,
    body: dict,
    x_goog_channel_token: str | None = Header(None),
    service: GmailIntakeService = Depends(get_service),
) -> None:
    config = service.config
    if config.pubsub_verification_token and x_goog_channel_token != config.pubsub_verification_token:
        raise HTTPException(status_code=401, detail="invalid token")

    message = body.get("message", {})
    data = message.get("data")
    if not data:
        return
    decoded = base64.b64decode(data).decode()
    info: Any = json.loads(decoded)
    history_id = info.get("historyId")
    LOGGER.info("gmail_push", extra={"historyId": history_id})
    # In real implementation we would fetch history and process messages
    # Here we simply trigger polling in background
    background.add_task(service.run_once)


__all__ = ["router"]
