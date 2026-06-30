"""Progress persistence for the ICA mock assessment (stdlib sqlite3).

Stores, per challenge, the highest level the candidate has completed (i.e. all
public tests up to that level passed). A level N is "unlocked" when
completed_level >= N - 1. Single-user, local; the DB lives in workspace/.
"""

import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "workspace" / "progress.db"
DEFAULT_CHALLENGE = "default"


def _conn() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS progress ("
        "  challenge TEXT PRIMARY KEY,"
        "  completed_level INTEGER NOT NULL"
        ")"
    )
    return conn


def get_completed(challenge: str = DEFAULT_CHALLENGE) -> int:
    """Highest completed level (0 if none completed yet)."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT completed_level FROM progress WHERE challenge = ?", (challenge,)
        ).fetchone()
    return row[0] if row else 0


def set_completed(level: int, challenge: str = DEFAULT_CHALLENGE) -> None:
    """Record that the candidate has completed up to `level` (monotonic)."""
    current = get_completed(challenge)
    level = max(current, level)
    with _conn() as conn:
        conn.execute(
            "INSERT INTO progress (challenge, completed_level) VALUES (?, ?) "
            "ON CONFLICT(challenge) DO UPDATE SET completed_level = excluded.completed_level",
            (challenge, level),
        )


def reset(challenge: str = DEFAULT_CHALLENGE) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM progress WHERE challenge = ?", (challenge,))
