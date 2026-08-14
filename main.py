#!/usr/bin/env python3
"""Local web IDE for coding assessments (single user, runs on your machine).

    python main.py          # serve at http://localhost:5000

An assessment format (see src/formats/) owns what a challenge looks like and how
an attempt is graded. This module owns routing, gating and persistence, and never
learns the vocabulary of a format: it speaks stages, files and attempts.

Routes:
    /                                     format list (landing)
    /<format>                             challenge list for a format
    /<format>/<challenge>                 attempts list for a challenge
    /<format>/<challenge>/run/<run_id>    the IDE for a specific attempt
    /ui/<file>                            static frontend assets
    /api/formats                          formats + challenge counts
    /api/<format>/challenges              challenges + attempt aggregates
    /api/<format>/<challenge>/runs        GET list attempts (newest first) / POST start one
    /api/<format>/<challenge>/run/<run_id>/...
                                          per-attempt API (state, stage, file, autosave, run)

Each attempt (run) has its own timer, progress gating and solution snapshot.
Finished runs are read-only (enforced server-side). Files a format does not
expose — hidden tests, starter templates — are never served.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from flask import Flask, abort, jsonify, request, send_from_directory

import formats
import runner_core as core
import runs

UI_DIR = core.ROOT / "ui"
HOST = os.environ.get("ICA_HOST", "127.0.0.1")
PORT = int(os.environ.get("ICA_PORT", "5000"))

app = Flask(__name__, static_folder=None)


def _require_format(fmt: str):
    """The format module for this URL segment, or 404."""
    module = formats.get(fmt)
    if module is None:
        abort(404)
    return module


def _require_challenge(fmt: str, challenge: str):
    """(format module, challenge dir) for an existing challenge, or 404."""
    module = _require_format(fmt)
    if not core.is_challenge(fmt, challenge):
        abort(404)
    return module, core.challenge_dir(fmt, challenge)


def _require_run(fmt: str, challenge: str, run_id: int):
    """(format module, challenge dir, run) for a run of THIS challenge, or 404."""
    module, cdir = _require_challenge(fmt, challenge)
    run = runs.get_run(run_id)
    if run is None or run["format"] != fmt or run["challenge"] != challenge:
        abort(404)
    return module, cdir, run


def unlocked_stages_for_run(module, cdir: Path, run: dict) -> list[int]:
    """Stages visible in this run: 1..(completed + 1), if authored."""
    return [n for n in module.stages(cdir) if n <= run["completed_stages"] + 1]


def _run_summary(run: dict) -> dict:
    """Fields for the attempts list (no solution body)."""
    return {
        "id": run["id"],
        "number": run["number"],
        "archived": bool(run["archived"]),
        "status": run["status"],
        "started_at": run["started_at"],
        "ended_at": run["ended_at"],
        "duration_seconds": run["duration_seconds"],
        "completed_stages": run["completed_stages"],
        "total_stages": run["total_stages"],
        "remaining_seconds": runs.remaining_seconds(run),
    }


# ----- pages + static -----

@app.get("/")
def home():
    return send_from_directory(UI_DIR, "formats.html")


@app.get("/ui/<path:filename>")
def static_files(filename: str):
    return send_from_directory(UI_DIR, filename)


@app.get("/<fmt>")
def challenges_page(fmt: str):
    _require_format(fmt)
    return send_from_directory(UI_DIR, "challenges.html")


@app.get("/<fmt>/<challenge>")
def attempts_page(fmt: str, challenge: str):
    _require_challenge(fmt, challenge)
    return send_from_directory(UI_DIR, "attempts.html")


@app.get("/<fmt>/<challenge>/run/<int:run_id>")
def ide(fmt: str, challenge: str, run_id: int):
    _require_run(fmt, challenge, run_id)
    return send_from_directory(UI_DIR, "index.html")


# ----- API: formats + challenges + attempts -----

@app.get("/api/formats")
def formats_list():
    out = []
    for info in formats.infos():
        challenges = core.list_challenges(info["id"])
        attempts = sum(runs.summary(info["id"], c["id"])["attempts"] for c in challenges)
        out.append({**info, "challenges": len(challenges), "attempts": attempts})
    return jsonify(out)


@app.get("/api/<fmt>/challenges")
def challenges(fmt: str):
    module = _require_format(fmt)
    out = []
    for c in core.list_challenges(fmt):
        cdir = core.challenge_dir(fmt, c["id"])
        out.append(
            {
                **c,
                "stages": len(module.stages(cdir)),
                "stage_label": module.STAGE_LABEL,
                **runs.summary(fmt, c["id"]),
            }
        )
    return jsonify({"format": {"id": fmt, "title": module.TITLE}, "challenges": out})


@app.get("/api/<fmt>/<challenge>/runs")
def list_runs(fmt: str, challenge: str):
    module, cdir = _require_challenge(fmt, challenge)
    meta = core.read_challenge_meta(fmt, challenge)
    include_archived = request.args.get("all") in ("1", "true")
    return jsonify(
        {
            "title": meta.get("title"),
            "timebox_minutes": meta.get("timebox_minutes"),
            "total_stages": len(module.stages(cdir)),
            "stage_label": module.STAGE_LABEL,
            "include_archived": include_archived,
            "runs": [
                _run_summary(r) for r in runs.list_runs(fmt, challenge, include_archived)
            ],
        }
    )


@app.post("/api/<fmt>/<challenge>/run/<int:run_id>/archive")
def archive_run(fmt: str, challenge: str, run_id: int):
    _require_run(fmt, challenge, run_id)
    runs.set_archived(run_id, True)
    return jsonify({"ok": True})


@app.post("/api/<fmt>/<challenge>/run/<int:run_id>/unarchive")
def unarchive_run(fmt: str, challenge: str, run_id: int):
    _require_run(fmt, challenge, run_id)
    runs.set_archived(run_id, False)
    return jsonify({"ok": True})


@app.post("/api/<fmt>/<challenge>/runs")
def start_run(fmt: str, challenge: str):
    module, cdir = _require_challenge(fmt, challenge)
    meta = core.read_challenge_meta(fmt, challenge)
    run_id = runs.create_run(
        fmt,
        challenge,
        module.new_solution(cdir),
        int(meta.get("timebox_minutes", 60)),
        len(module.stages(cdir)),
    )
    return jsonify({"run_id": run_id})


# ----- API: per-run -----

@app.get("/api/<fmt>/<challenge>/run/<int:run_id>/state")
def state(fmt: str, challenge: str, run_id: int):
    module, cdir, run = _require_run(fmt, challenge, run_id)
    meta = core.read_challenge_meta(fmt, challenge)
    stages = unlocked_stages_for_run(module, cdir, run)
    return jsonify(
        {
            "format": fmt,
            "challenge": challenge,
            "run_id": run_id,
            "number": run["number"],
            "status": run["status"],
            "read_only": run["status"] != "in_progress",
            "stages": stages,
            "stage_label": module.STAGE_LABEL,
            "current": stages[-1] if stages else None,
            "completed": run["completed_stages"],
            "total_stages": run["total_stages"],
            "solution": run["solution"],
            "title": meta.get("title"),
            "timebox_minutes": meta.get("timebox_minutes"),
            "remaining_seconds": runs.remaining_seconds(run),
            "elapsed_seconds": runs.elapsed_seconds(run),
            "started_at": run["started_at"],
            "ended_at": run["ended_at"],
            "duration_seconds": run["duration_seconds"],
            "challenge_complete": run["status"] == "completed",
            "over_time": runs.elapsed_seconds(run) > int(meta.get("timebox_minutes", 60)) * 60,
        }
    )


@app.get("/api/<fmt>/<challenge>/run/<int:run_id>/stage/<int:n>")
def stage(fmt: str, challenge: str, run_id: int, n: int):
    module, cdir, run = _require_run(fmt, challenge, run_id)
    if n not in unlocked_stages_for_run(module, cdir, run):
        return jsonify({"error": "locked"}), 404
    return jsonify({"stage": n, "doc_md": module.stage_doc(cdir, n)})


@app.get("/api/<fmt>/<challenge>/run/<int:run_id>/files")
def files(fmt: str, challenge: str, run_id: int):
    module, cdir, run = _require_run(fmt, challenge, run_id)
    return jsonify(module.files(cdir, unlocked_stages_for_run(module, cdir, run)))


@app.get("/api/<fmt>/<challenge>/run/<int:run_id>/file/<file_id>")
def file(fmt: str, challenge: str, run_id: int, file_id: str):
    module, cdir, run = _require_run(fmt, challenge, run_id)
    gated_by = module.stage_of_file(file_id)
    if gated_by is not None and gated_by not in unlocked_stages_for_run(module, cdir, run):
        return jsonify({"error": "locked"}), 404
    content = module.read_file(cdir, file_id)
    if content is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": file_id, "content": content})


def _reject_if_not_active(run: dict):
    """Reject editing/running only for finished attempts. The timebox is a target,
    not a lock: an in-progress run stays editable/runnable even past the limit."""
    if run["status"] != "in_progress":
        return jsonify({"error": "read_only"}), 403
    return None


@app.post("/api/<fmt>/<challenge>/run/<int:run_id>/resume")
def resume_run(fmt: str, challenge: str, run_id: int):
    """Start the clock for this attempt (opening/returning to its IDE)."""
    _, _, run = _require_run(fmt, challenge, run_id)
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


@app.post("/api/<fmt>/<challenge>/run/<int:run_id>/pause")
def pause_run(fmt: str, challenge: str, run_id: int):
    """Stop the clock for this attempt (leaving/hiding it)."""
    _, _, run = _require_run(fmt, challenge, run_id)
    if run["status"] == "in_progress":
        runs.pause(run_id)
    return jsonify({"ok": True})


@app.post("/api/<fmt>/<challenge>/run/<int:run_id>/autosave")
def autosave(fmt: str, challenge: str, run_id: int):
    _, _, run = _require_run(fmt, challenge, run_id)
    rejection = _reject_if_not_active(run)
    if rejection:
        return rejection
    runs.update_solution(run_id, request.get_json(force=True).get("code", ""))
    return jsonify({"ok": True, "remaining_seconds": runs.remaining_seconds(run)})


@app.post("/api/<fmt>/<challenge>/run/<int:run_id>/run")
def run_tests(fmt: str, challenge: str, run_id: int):
    module, cdir, run = _require_run(fmt, challenge, run_id)
    rejection = _reject_if_not_active(run)
    if rejection:
        return rejection

    data = request.get_json(force=True)
    target = int(data.get("stage", 1))
    if target not in unlocked_stages_for_run(module, cdir, run):
        return jsonify({"error": "stage locked"}), 400
    if "code" in data:
        runs.update_solution(run_id, data["code"])
        run = runs.get_run(run_id)

    unlocked_before = set(unlocked_stages_for_run(module, cdir, run))
    # The run's snapshot is the source of truth for its code; the format puts it
    # on disk and decides whether this stage passes.
    result = module.run_stage(cdir, target, run["solution"])
    if result["passed"]:
        runs.set_completed_stages(run_id, target)

    run = runs.get_run(run_id)
    if run["completed_stages"] >= run["total_stages"]:
        runs.mark_completed(run_id)
        run = runs.get_run(run_id)

    unlocked = unlocked_stages_for_run(module, cdir, run)
    newly = sorted(set(unlocked) - unlocked_before)
    return jsonify(
        {
            **result,
            "completed": run["completed_stages"],
            "unlocked": unlocked,
            "unlocked_now": newly[-1] if newly else None,
            "challenge_complete": run["status"] == "completed",
            "status": run["status"],
            "duration_seconds": run["duration_seconds"],
            "ended_at": run["ended_at"],
            "over_time": bool(run["duration_seconds"])
            and run["duration_seconds"] > run["timebox_minutes"] * 60,
        }
    )


if __name__ == "__main__":
    print(f"Assessment IDE at http://{HOST}:{PORT}  (Ctrl+C to quit)")
    app.run(host=HOST, port=PORT, threaded=True)
