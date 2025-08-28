import base64

from graniteledger.integrations.gmail_intake.normalizer import normalize_message
from graniteledger.integrations.gmail_intake.parser import parse_body
from graniteledger.integrations.gmail_intake.models import Body, Attachment


def test_normalize_message_basic():
    body_text = base64.urlsafe_b64encode(b'Hello').decode()
    msg = {
        'id': 'm1',
        'threadId': 't1',
        'historyId': 'h1',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'Sender <s@example.com>'},
                {'name': 'To', 'value': 'Me <me@example.com>'},
                {'name': 'Subject', 'value': 'Invoice 1'},
                {'name': 'Date', 'value': 'Mon, 1 Jan 2024 00:00:00 +0000'},
            ],
            'parts': [
                {'mimeType': 'text/plain', 'body': {'data': body_text}},
            ],
        },
    }
    body = parse_body(msg['payload'])
    env = normalize_message(msg, body, [])
    assert env.gmail.id == 'm1'
    assert env.subject == 'Invoice 1'
    assert env.body.text_preview == 'Hello'
