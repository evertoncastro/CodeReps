"""Attempt (run) persistence for the ICA mock assessment (stdlib sqlite3).

Each time a candidate starts a challenge, a run is created. A run holds its own
timer (started_at + timebox), its own progress (completed_level), and its own
solution snapshot (the source of truth for that attempt's code). Runs are
per-challenge history; the landing page lists them newest-first.

Single-user, local; the DB is challenges/progress.db (shared with the old
progress table, which is no longer used).
"""

import sqlite3
import time
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "challenges" / "progress.db"


def _conn() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS runs ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  challenge TEXT NOT NULL,"
        "  status TEXT NOT NULL DEFAULT 'in_progress',"  # in_progress | completed | expired
        "  started_at REAL NOT NULL,"
        "  ended_at REAL,"
        "  duration_seconds REAL,"
        "  completed_level INTEGER NOT NULL DEFAULT 0,"
        "  total_levels INTEGER NOT NULL,"
        "  timebox_minutes INTEGER NOT NULL,"
        "  initial_solution TEXT NOT NULL DEFAULT '',"
        "  solution TEXT NOT NULL DEFAULT ''"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_challenge ON runs(challenge, id DESC)")
    return conn


def _maybe_expire(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """Lazily mark a run expired once its timebox has elapsed (no background job)."""
    run = dict(row)
    if run["status"] == "in_progress":
        deadline = run["started_at"] + run["timebox_minutes"] * 60
        if time.time() >= deadline:
            run["status"] = "expired"
            run["ended_at"] = deadline
            run["duration_seconds"] = run["timebox_minutes"] * 60
            conn.execute(
                "UPDATE runs SET status='expired', ended_at=?, duration_seconds=? WHERE id=?",
                (run["ended_at"], run["duration_seconds"], run["id"]),
            )
    return run


def create_run(challenge: str, initial_solution: str, timebox_minutes: int,
               total_levels: int) -> int:
    now = time.time()
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO runs (challenge, status, started_at, completed_level, "
            "total_levels, timebox_minutes, initial_solution, solution) "
            "VALUES (?, 'in_progress', ?, 0, ?, ?, ?, ?)",
            (challenge, now, total_levels, timebox_minutes, initial_solution, initial_solution),
        )
        return cur.lastrowid


def get_run(run_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return _maybe_expire(conn, row) if row is not None else None


def list_runs(challenge: str) -> list[dict]:
    """All runs for a challenge, newest first."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM runs WHERE challenge = ? ORDER BY id DESC", (challenge,)
        ).fetchall()
        return [_maybe_expire(conn, r) for r in rows]


def update_solution(run_id: int, code: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE runs SET solution = ? WHERE id = ?", (code, run_id))


def set_completed_level(run_id: int, level: int) -> None:
    """Record the highest level passed in this run (monotonic)."""
    with _conn() as conn:
        conn.execute(
            "UPDATE runs SET completed_level = MAX(completed_level, ?) WHERE id = ?",
            (level, run_id),
        )


def mark_completed(run_id: int) -> None:
    """Mark a run completed in time, recording end time and duration."""
    now = time.time()
    with _conn() as conn:
        conn.execute(
            "UPDATE runs SET status='completed', ended_at=?, "
            "duration_seconds = ? - started_at WHERE id = ? AND status = 'in_progress'",
            (now, now, run_id),
        )


def remaining_seconds(run: dict) -> int:
    """Seconds left in this run's timebox (0 once not in progress)."""
    if run["status"] != "in_progress":
        return 0
    return max(0, int(run["timebox_minutes"] * 60 - (time.time() - run["started_at"])))


def summary(challenge: str) -> dict:
    """Aggregate for the challenge list: attempt count, best progress, active run."""
    runs = list_runs(challenge)
    return {
        "attempts": len(runs),
        "best_completed": max((r["completed_level"] for r in runs), default=0),
        "has_active": any(r["status"] == "in_progress" for r in runs),
    }
