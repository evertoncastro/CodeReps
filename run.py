#!/usr/bin/env python3
"""Local web IDE for ICA mock assessments (single user, runs on your machine).

    python run.py           # serve at http://localhost:5000

Routes:
    /                       challenge list (landing page)
    /<challenge>            the IDE for that challenge (e.g. /warehouse_inventory)
    /ui/<file>             static frontend assets
    /api/challenges         list challenges + progress
    /api/<challenge>/...    per-challenge API (state, level, file, save, run)

Progression is gated per challenge: only unlocked levels are exposed and, once
the timebox expires, run/save are rejected. Hidden test sources are never served.
"""

import os
import re
import time

from flask import Flask, abort, jsonify, request, send_from_directory

import progress
import runner_core as core

UI_DIR = core.BASE / "ui"
HOST = os.environ.get("ICA_HOST", "127.0.0.1")
PORT = int(os.environ.get("ICA_PORT", "5000"))

app = Flask(__name__, static_folder=None)


def _require(challenge: str) -> None:
    if not core.is_challenge(challenge):
        abort(404)


def unlocked_levels(challenge: str) -> list[int]:
    """Levels the candidate may currently see: 1..(completed + 1), if authored."""
    completed = progress.get_completed(challenge)
    return [n for n in core.available_levels(challenge) if n <= completed + 1]


def remaining_seconds(challenge: str) -> int:
    """Seconds left in the timebox (0 once expired). Starts the timer."""
    meta = core.read_challenge_meta(challenge)
    started = progress.ensure_started(challenge)
    timebox = int(meta.get("timebox_minutes", 60)) * 60
    return max(0, int(timebox - (time.time() - started)))


def is_complete(challenge: str) -> bool:
    """Whether every authored level has been completed."""
    authored = core.available_levels(challenge)
    return bool(authored) and progress.get_completed(challenge) >= max(authored)


# ----- pages + static -----

@app.get("/")
def home():
    return send_from_directory(UI_DIR, "challenges.html")


@app.get("/ui/<path:filename>")
def static_files(filename: str):
    return send_from_directory(UI_DIR, filename)


@app.get("/<challenge>")
def ide(challenge: str):
    _require(challenge)
    return send_from_directory(UI_DIR, "index.html")


# ----- API -----

@app.get("/api/challenges")
def challenges():
    out = []
    for c in core.list_challenges():
        cid = c["id"]
        started = progress.get_started_at(cid)
        meta_remaining = None
        if started is not None:
            timebox = int(c.get("timebox_minutes") or 60) * 60
            meta_remaining = max(0, int(timebox - (time.time() - started)))
        out.append(
            {
                **c,
                "completed": progress.get_completed(cid),
                "started": started is not None,
                "remaining_seconds": meta_remaining,
            }
        )
    return jsonify(out)


@app.get("/api/<challenge>/state")
def state(challenge: str):
    _require(challenge)
    levels = unlocked_levels(challenge)
    meta = core.read_challenge_meta(challenge)
    return jsonify(
        {
            "challenge": challenge,
            "levels": levels,
            "current": levels[-1] if levels else None,
            "completed": progress.get_completed(challenge),
            "authored": core.available_levels(challenge),
            "solution": core.read_solution(challenge),
            "title": meta.get("title"),
            "timebox_minutes": meta.get("timebox_minutes"),
            "remaining_seconds": remaining_seconds(challenge),
            "challenge_complete": is_complete(challenge),
        }
    )


@app.get("/api/<challenge>/level/<int:n>")
def level(challenge: str, n: int):
    _require(challenge)
    if n not in unlocked_levels(challenge):
        return jsonify({"error": "locked"}), 404
    return jsonify(
        {
            "level": n,
            "readme_md": core.read_readme(challenge, n),
            "public_test_src": core.read_public_source(challenge, n),
        }
    )


@app.get("/api/<challenge>/files")
def files(challenge: str):
    _require(challenge)
    return jsonify(core.list_files(challenge, unlocked_levels(challenge)))


@app.get("/api/<challenge>/file/<file_id>")
def file(challenge: str, file_id: str):
    _require(challenge)
    m = re.fullmatch(r"public-(\d+)", file_id)
    if m and int(m.group(1)) not in unlocked_levels(challenge):
        return jsonify({"error": "locked"}), 404
    content = core.read_file(challenge, file_id)
    if content is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": file_id, "content": content})


@app.post("/api/<challenge>/restart")
def restart(challenge: str):
    """Restart the challenge: back to level 1 with a fresh timer. The
    solution file is intentionally kept."""
    _require(challenge)
    progress.reset(challenge)
    return jsonify(
        {
            "levels": unlocked_levels(challenge),
            "remaining_seconds": remaining_seconds(challenge),
        }
    )


@app.post("/api/<challenge>/save")
def save(challenge: str):
    _require(challenge)
    if remaining_seconds(challenge) <= 0:
        return jsonify({"error": "time_up"}), 403
    data = request.get_json(force=True)
    core.write_solution(challenge, data.get("code", ""))
    return jsonify({"ok": True})


@app.post("/api/<challenge>/run")
def run(challenge: str):
    _require(challenge)
    if remaining_seconds(challenge) <= 0:
        return jsonify({"error": "time_up", "remaining_seconds": 0}), 403
    data = request.get_json(force=True)
    target = int(data.get("level", 1))
    if target not in unlocked_levels(challenge):
        return jsonify({"error": "level locked"}), 400
    if "code" in data:
        core.write_solution(challenge, data["code"])

    unlocked_before = set(unlocked_levels(challenge))
    public = core.run_public(challenge, target)
    hidden = core.run_hidden(challenge, target)

    # Both public and hidden tests (levels 1..target) must pass to advance.
    if public["passed"] and hidden["passed"]:
        progress.set_completed(target, challenge)

    unlocked = unlocked_levels(challenge)
    newly = sorted(set(unlocked) - unlocked_before)
    return jsonify(
        {
            "public": public,
            "hidden": hidden,
            "completed": progress.get_completed(challenge),
            "unlocked": unlocked,
            "unlocked_now": newly[-1] if newly else None,
            "challenge_complete": is_complete(challenge),
        }
    )


if __name__ == "__main__":
    print(f"ICA IDE at http://{HOST}:{PORT}  (Ctrl+C to quit)")
    app.run(host=HOST, port=PORT, threaded=True)
