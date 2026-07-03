#!/usr/bin/env python3
"""Local web IDE for ICA mock assessments (single user, runs on your machine).

    python run.py           # serve at http://localhost:5000

Routes:
    /                                    challenge list (landing)
    /<challenge>                         attempts list for a challenge
    /<challenge>/run/<run_id>            the IDE for a specific attempt
    /ui/<file>                           static frontend assets
    /api/challenges                      challenges + attempt aggregates
    /api/<challenge>/runs                GET list attempts (newest first) / POST start one
    /api/<challenge>/run/<run_id>/...    per-attempt API (state, level, file, autosave, run)

Each attempt (run) has its own timer, progress gating and solution snapshot.
Finished/expired runs are read-only (enforced server-side). Hidden test sources
and the solution template are never served.
"""

import os
import re
import time

from flask import Flask, abort, jsonify, request, send_from_directory

import runner_core as core
import runs

UI_DIR = core.BASE / "ui"
HOST = os.environ.get("ICA_HOST", "127.0.0.1")
PORT = int(os.environ.get("ICA_PORT", "5000"))

app = Flask(__name__, static_folder=None)


def _require(challenge: str) -> None:
    if not core.is_challenge(challenge):
        abort(404)


def _require_run(challenge: str, run_id: int) -> dict:
    _require(challenge)
    run = runs.get_run(run_id)
    if run is None or run["challenge"] != challenge:
        abort(404)
    return run


def unlocked_levels_for_run(run: dict) -> list[int]:
    """Levels visible in this run: 1..(completed + 1), if authored."""
    return [n for n in core.available_levels(run["challenge"]) if n <= run["completed_level"] + 1]


def _run_summary(run: dict) -> dict:
    """Fields for the attempts list (no solution body)."""
    return {
        "id": run["id"],
        "status": run["status"],
        "started_at": run["started_at"],
        "ended_at": run["ended_at"],
        "duration_seconds": run["duration_seconds"],
        "completed_level": run["completed_level"],
        "total_levels": run["total_levels"],
        "remaining_seconds": runs.remaining_seconds(run),
    }


# ----- pages + static -----

@app.get("/")
def home():
    return send_from_directory(UI_DIR, "challenges.html")


@app.get("/ui/<path:filename>")
def static_files(filename: str):
    return send_from_directory(UI_DIR, filename)


@app.get("/<challenge>")
def attempts_page(challenge: str):
    _require(challenge)
    return send_from_directory(UI_DIR, "attempts.html")


@app.get("/<challenge>/run/<int:run_id>")
def ide(challenge: str, run_id: int):
    _require_run(challenge, run_id)
    return send_from_directory(UI_DIR, "index.html")


# ----- API: challenges + attempts -----

@app.get("/api/challenges")
def challenges():
    out = []
    for c in core.list_challenges():
        out.append({**c, **runs.summary(c["id"])})
    return jsonify(out)


@app.get("/api/<challenge>/runs")
def list_runs(challenge: str):
    _require(challenge)
    meta = core.read_challenge_meta(challenge)
    return jsonify(
        {
            "title": meta.get("title"),
            "timebox_minutes": meta.get("timebox_minutes"),
            "total_levels": len(core.available_levels(challenge)),
            "runs": [_run_summary(r) for r in runs.list_runs(challenge)],
        }
    )


@app.post("/api/<challenge>/runs")
def start_run(challenge: str):
    _require(challenge)
    meta = core.read_challenge_meta(challenge)
    total = len(core.available_levels(challenge))
    code = core.create_solution_from_template(challenge)
    run_id = runs.create_run(challenge, code, int(meta.get("timebox_minutes", 60)), total)
    return jsonify({"run_id": run_id})


# ----- API: per-run -----

@app.get("/api/<challenge>/run/<int:run_id>/state")
def state(challenge: str, run_id: int):
    run = _require_run(challenge, run_id)
    meta = core.read_challenge_meta(challenge)
    levels = unlocked_levels_for_run(run)
    # For an active run, make solution.py on disk match this run before tests.
    if run["status"] == "in_progress":
        core.write_solution(challenge, run["solution"])
    return jsonify(
        {
            "challenge": challenge,
            "run_id": run_id,
            "status": run["status"],
            "read_only": run["status"] != "in_progress",
            "levels": levels,
            "current": levels[-1] if levels else None,
            "completed": run["completed_level"],
            "authored": core.available_levels(challenge),
            "total_levels": run["total_levels"],
            "solution": run["solution"],
            "title": meta.get("title"),
            "timebox_minutes": meta.get("timebox_minutes"),
            "remaining_seconds": runs.remaining_seconds(run),
            "started_at": run["started_at"],
            "ended_at": run["ended_at"],
            "duration_seconds": run["duration_seconds"],
            "challenge_complete": run["status"] == "completed",
        }
    )


@app.get("/api/<challenge>/run/<int:run_id>/level/<int:n>")
def level(challenge: str, run_id: int, n: int):
    run = _require_run(challenge, run_id)
    if n not in unlocked_levels_for_run(run):
        return jsonify({"error": "locked"}), 404
    return jsonify(
        {
            "level": n,
            "readme_md": core.read_readme(challenge, n),
            "public_test_src": core.read_public_source(challenge, n),
        }
    )


@app.get("/api/<challenge>/run/<int:run_id>/files")
def files(challenge: str, run_id: int):
    run = _require_run(challenge, run_id)
    return jsonify(core.list_files(challenge, unlocked_levels_for_run(run)))


@app.get("/api/<challenge>/run/<int:run_id>/file/<file_id>")
def file(challenge: str, run_id: int, file_id: str):
    run = _require_run(challenge, run_id)
    m = re.fullmatch(r"public-(\d+)", file_id)
    if m and int(m.group(1)) not in unlocked_levels_for_run(run):
        return jsonify({"error": "locked"}), 404
    content = core.read_file(challenge, file_id)
    if content is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": file_id, "content": content})


def _reject_if_not_active(run: dict):
    """Return a (json, status) 403 tuple if the run can't be modified, else None."""
    if run["status"] == "expired":
        return jsonify({"error": "time_up"}), 403
    if run["status"] != "in_progress":
        return jsonify({"error": "read_only"}), 403
    return None


@app.post("/api/<challenge>/run/<int:run_id>/resume")
def resume_run(challenge: str, run_id: int):
    """Start the clock for this attempt (opening/returning to its IDE)."""
    run = _require_run(challenge, run_id)
    if run["status"] == "in_progress":
        runs.resume(run_id)
        run = runs.get_run(run_id)
    return jsonify(
        {
            "status": run["status"],
            "read_only": run["status"] != "in_progress",
            "remaining_seconds": runs.remaining_seconds(run),
        }
    )


@app.post("/api/<challenge>/run/<int:run_id>/pause")
def pause_run(challenge: str, run_id: int):
    """Stop the clock for this attempt (leaving/hiding it)."""
    run = _require_run(challenge, run_id)
    if run["status"] == "in_progress":
        runs.pause(run_id)
    return jsonify({"ok": True})


@app.post("/api/<challenge>/run/<int:run_id>/autosave")
def autosave(challenge: str, run_id: int):
    run = _require_run(challenge, run_id)
    rejection = _reject_if_not_active(run)
    if rejection:
        return rejection
    code = request.get_json(force=True).get("code", "")
    runs.update_solution(run_id, code)
    core.write_solution(challenge, code)  # keep disk == DB for the active run
    return jsonify({"ok": True, "remaining_seconds": runs.remaining_seconds(run)})


@app.post("/api/<challenge>/run/<int:run_id>/run")
def run_tests(challenge: str, run_id: int):
    run = _require_run(challenge, run_id)
    rejection = _reject_if_not_active(run)
    if rejection:
        return rejection

    data = request.get_json(force=True)
    target = int(data.get("level", 1))
    if target not in unlocked_levels_for_run(run):
        return jsonify({"error": "level locked"}), 400
    if "code" in data:
        runs.update_solution(run_id, data["code"])
        core.write_solution(challenge, data["code"])

    unlocked_before = set(unlocked_levels_for_run(run))
    public = core.run_public(challenge, target)
    hidden = core.run_hidden(challenge, target)

    # Both public and hidden tests (levels 1..target) must pass to advance.
    if public["passed"] and hidden["passed"]:
        runs.set_completed_level(run_id, target)

    run = runs.get_run(run_id)
    if run["completed_level"] >= run["total_levels"]:
        runs.mark_completed(run_id)
        run = runs.get_run(run_id)

    unlocked = unlocked_levels_for_run(run)
    newly = sorted(set(unlocked) - unlocked_before)
    return jsonify(
        {
            "public": public,
            "hidden": hidden,
            "completed": run["completed_level"],
            "unlocked": unlocked,
            "unlocked_now": newly[-1] if newly else None,
            "challenge_complete": run["status"] == "completed",
            "status": run["status"],
            "duration_seconds": run["duration_seconds"],
            "ended_at": run["ended_at"],
        }
    )


if __name__ == "__main__":
    print(f"ICA IDE at http://{HOST}:{PORT}  (Ctrl+C to quit)")
    app.run(host=HOST, port=PORT, threaded=True)
