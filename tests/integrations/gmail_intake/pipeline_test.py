import json

import pytest
httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from fastapi import FastAPI

from graniteledger.integrations.gmail_intake.pipeline import sign_payload
from graniteledger.integrations.gmail_intake.config import GmailIntakeConfig
from api.routes.intake_email import router


def test_hmac_signature_verification(tmp_path, monkeypatch):
    cfg = GmailIntakeConfig(
        invoice_sender='s', oauth_client_json='x', token_json='y',
        intake_url='http://example.com', shared_secret='secret', state_db=tmp_path/'db.db'
    )
    payload = json.dumps({'a':1}).encode()
    sig = sign_payload(cfg.shared_secret, payload)
    assert sig.startswith('sha256=')


def test_intake_endpoint_verifies_hmac(monkeypatch, tmp_path):
    monkeypatch.setenv('GL_SHARED_SECRET','secret')
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = json.dumps({'gmail': {'id':'1'}, 'from':'a', 'body': {'text_preview':'x'}})
    sig = sign_payload('secret', body.encode())
    resp = client.post('/api/intake/email-invoice', data=body, headers={'X-GL-Signature': sig})
    assert resp.status_code == 201
