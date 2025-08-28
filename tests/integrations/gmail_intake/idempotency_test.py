from pathlib import Path

from graniteledger.integrations.gmail_intake.state import StateDB


def test_idempotency(tmp_path):
    db = StateDB(tmp_path / 'state.db')
    assert not db.has_processed('a')
    db.mark_processed('a', 200)
    assert db.has_processed('a')
