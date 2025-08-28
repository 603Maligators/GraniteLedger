import base64
import json

import pytest
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from fastapi import FastAPI

from graniteledger.integrations.gmail_intake.pubsub_server import router


def test_push_verification(monkeypatch):
    monkeypatch.setenv('GL_PUBSUB_VERIFICATION_TOKEN','token')
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    data = base64.b64encode(json.dumps({'historyId':'1'}).encode()).decode()
    resp = client.post('/gmail/push', json={'message': {'data': data}}, headers={'X-Goog-Channel-Token':'token'})
    assert resp.status_code == 204
