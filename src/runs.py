"""Attempt (run) persistence for the ICA mock assessment (stdlib sqlite3).

Each time a candidate starts a challenge, a run is created. A run holds its own
timer (started_at + timebox), its own progress (completed_level), and its own
solution snapshot (the source of truth for that attempt's code). Runs are
per-challenge history; the landing page lists them newest-first.

Single-user, local; the DB is challenges/progress.db (shared with the old
progress table, which is no longer used).
"""

import os
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent  # project root (src/ -> root)
# ICA_DB lets tests point at a throwaway DB so they never touch real progress.
DB = Path(os.environ.get("ICA_DB") or ROOT / "challenges" / "progress.db")


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
        "  spent_seconds REAL NOT NULL DEFAULT 0,"   # active time already accumulated (while paused)
        "  resumed_at REAL,"                          # start of the current active session; NULL when paused
        "  completed_level INTEGER NOT NULL DEFAULT 0,"
        "  total_levels INTEGER NOT NULL,"
        "  timebox_minutes INTEGER NOT NULL,"
        "  initial_solution TEXT NOT NULL DEFAULT '',"
        "  solution TEXT NOT NULL DEFAULT ''"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_challenge ON runs(challenge, id DESC)")
    # Migrate older DBs that predate the pause/resume columns.
    cols = [r[1] for r in conn.execute("PRAGMA table_info(runs)").fetchall()]
    if "spent_seconds" not in cols:
        conn.execute("ALTER TABLE runs ADD COLUMN spent_seconds REAL NOT NULL DEFAULT 0")
    if "resumed_at" not in cols:
        conn.execute("ALTER TABLE runs ADD COLUMN resumed_at REAL")
    return conn


def _active_spent(run: dict) -> float:
    """Active time used so far: accumulated + the current running session."""
    spent = run["spent_seconds"]
    if run["resumed_at"] is not None:
        spent += time.time() - run["resumed_at"]
    return spent


# The timebox is a target, not a hard stop: a run keeps accruing active time
# past the limit until the candidate completes it (that overtime is a metric).


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
        return dict(row) if row is not None else None


def list_runs(challenge: str) -> list[dict]:
    """All runs for a challenge, newest first."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM runs WHERE challenge = ? ORDER BY id DESC", (challenge,)
        ).fetchall()
        return [dict(r) for r in rows]


def delete_run(run_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))


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


def resume(run_id: int) -> None:
    """Start counting active time for this run (when its IDE is opened/visible)."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT status, resumed_at FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        if row and row["status"] == "in_progress" and row["resumed_at"] is None:
            conn.execute("UPDATE runs SET resumed_at = ? WHERE id = ?", (time.time(), run_id))


def pause(run_id: int) -> None:
    """Stop the clock: fold the current session into spent_seconds (on leave)."""
    now = time.time()
    with _conn() as conn:
        row = conn.execute(
            "SELECT status, spent_seconds, resumed_at FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        if row and row["status"] == "in_progress" and row["resumed_at"] is not None:
            spent = row["spent_seconds"] + (now - row["resumed_at"])
            conn.execute(
                "UPDATE runs SET spent_seconds = ?, resumed_at = NULL WHERE id = ?",
                (spent, run_id),
            )


def mark_completed(run_id: int) -> None:
    """Mark a run completed in time, recording end time and active duration."""
    now = time.time()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM runs WHERE id = ? AND status = 'in_progress'", (run_id,)
        ).fetchone()
        if row is None:
            return
        spent = row["spent_seconds"] + (now - row["resumed_at"] if row["resumed_at"] else 0)
        conn.execute(
            "UPDATE runs SET status='completed', ended_at=?, spent_seconds=?, "
            "resumed_at=NULL, duration_seconds=? WHERE id = ?",
            (now, spent, spent, run_id),
        )


def remaining_seconds(run: dict) -> int:
    """Seconds left in this run's timebox (may be NEGATIVE past the limit).

    Based on active time only (paused time does not count down). 0 once the run
    is no longer in progress."""
    if run["status"] != "in_progress":
        return 0
    return int(run["timebox_minutes"] * 60 - _active_spent(run))


def elapsed_seconds(run: dict) -> int:
    """Active time used so far (keeps growing past the timebox)."""
    if run["status"] != "in_progress":
        return int(run["duration_seconds"] or 0)
    return int(_active_spent(run))


def summary(challenge: str) -> dict:
    """Aggregate for the challenge list: attempt count, best progress, active run."""
    runs = list_runs(challenge)
    return {
        "attempts": len(runs),
        "best_completed": max((r["completed_level"] for r in runs), default=0),
        "has_active": any(r["status"] == "in_progress" for r in runs),
    }
