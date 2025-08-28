"""SQLite state management for Gmail intake."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS gmail_intake (
    gmail_message_id TEXT PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pipeline_status INTEGER,
    error TEXT
);
"""


class StateDB:
    """Helper around SQLite for idempotency."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _ensure(self) -> None:
        with self._connect() as conn:
            conn.execute(CREATE_TABLE_SQL)
            conn.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
        finally:
            conn.close()

    def has_processed(self, gmail_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT 1 FROM gmail_intake WHERE gmail_message_id = ?", (gmail_id,)
            )
            return cur.fetchone() is not None

    def mark_processed(self, gmail_id: str, status: int, error: Optional[str] = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO gmail_intake (gmail_message_id, pipeline_status, error)"
                " VALUES (?, ?, ?)",
                (gmail_id, status, error),
            )
            conn.commit()


__all__ = ["StateDB"]
