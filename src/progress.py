"""Progress + timer persistence for the ICA mock assessment (stdlib sqlite3).

Stores, per challenge:
  * the highest completed level (all public tests up to it passed),
  * when the candidate first started the challenge (epoch seconds), used to
    compute the remaining time of the challenge's timebox.

A level N is "unlocked" when completed_level >= N - 1. Single-user, local; the
DB lives in challenges/progress.db, keyed by challenge id.
"""

import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent  # project root (src/ -> root)
DB = ROOT / "challenges" / "progress.db"
DEFAULT_CHALLENGE = "default"


def _conn() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS progress ("
        "  challenge TEXT PRIMARY KEY,"
        "  completed_level INTEGER NOT NULL DEFAULT 0,"
        "  started_at REAL"
        ")"
    )
    # Migrate older DBs that predate the started_at column.
    cols = [r[1] for r in conn.execute("PRAGMA table_info(progress)").fetchall()]
    if "started_at" not in cols:
        conn.execute("ALTER TABLE progress ADD COLUMN started_at REAL")
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
    level = max(get_completed(challenge), level)
    with _conn() as conn:
        conn.execute(
            "INSERT INTO progress (challenge, completed_level) VALUES (?, ?) "
            "ON CONFLICT(challenge) DO UPDATE SET completed_level = excluded.completed_level",
            (challenge, level),
        )


def get_started_at(challenge: str = DEFAULT_CHALLENGE) -> float | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT started_at FROM progress WHERE challenge = ?", (challenge,)
        ).fetchone()
    return row[0] if row and row[0] is not None else None


def ensure_started(challenge: str = DEFAULT_CHALLENGE) -> float:
    """Start the challenge timer on first access; return its start time."""
    started = get_started_at(challenge)
    if started is not None:
        return started
    started = time.time()
    with _conn() as conn:
        if conn.execute(
            "SELECT 1 FROM progress WHERE challenge = ?", (challenge,)
        ).fetchone():
            conn.execute(
                "UPDATE progress SET started_at = ? WHERE challenge = ?",
                (started, challenge),
            )
        else:
            conn.execute(
                "INSERT INTO progress (challenge, completed_level, started_at) "
                "VALUES (?, 0, ?)",
                (challenge, started),
            )
    return started


def reset(challenge: str = DEFAULT_CHALLENGE) -> None:
    """Clear progress and timer for a challenge (fresh start)."""
    with _conn() as conn:
        conn.execute("DELETE FROM progress WHERE challenge = ?", (challenge,))
