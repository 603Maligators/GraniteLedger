from pathlib import Path

import pytest
pytest.importorskip("googleapiclient")
from graniteledger.integrations.gmail_intake.gmail_client import GmailClient
from graniteledger.integrations.gmail_intake.config import GmailIntakeConfig


class FakeExecute:
    def __init__(self, resp):
        self.resp = resp

    def execute(self):
        return self.resp


class FakeLabels:
    def __init__(self):
        self.labels = [{'id': '1', 'name': 'Existing'}]

    def list(self, userId):
        return FakeExecute({'labels': self.labels})

    def create(self, userId, body):
        lbl = {'id': str(len(self.labels)+1), 'name': body['name']}
        self.labels.append(lbl)
        return FakeExecute(lbl)


class FakeUsers:
    def __init__(self):
        self._labels = FakeLabels()

    def labels(self):
        return self._labels

    def messages(self):  # pragma: no cover - not used
        class _M:
            def list(self, **kwargs):
                return FakeExecute({'messages': []})

            def modify(self, **kwargs):
                return FakeExecute({})

        return _M()


class FakeService:
    def users(self):
        return FakeUsers()


def make_config(tmp_path):
    return GmailIntakeConfig(
        invoice_sender='s', oauth_client_json='x', token_json='y',
        intake_url='http://example.com', shared_secret='secret', state_db=tmp_path/'db.db'
    )


def test_get_label_id_creates(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    client = GmailClient(cfg, service=FakeService())
    lbl_id = client.get_label_id('NewLabel')
    assert lbl_id == '2'
