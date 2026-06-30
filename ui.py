#!/usr/bin/env python3
"""Local web IDE for the ICA mock assessment (single user, runs on your machine).

    python ui.py            # serve at http://localhost:5000

Provides a REST API to read challenge state, save solution.py, and run tests
(structured pass/fail), reusing runner_core (same execution path as the CLI).

Progression is gated: only unlocked levels (up to completed + 1) are exposed.
Hidden test sources are never served. Tests run in a subprocess via runner_core.
"""

import os
import re

from flask import Flask, jsonify, request, send_from_directory

import progress
import runner_core as core

UI_DIR = core.BASE / "ui"
HOST = os.environ.get("ICA_HOST", "127.0.0.1")
PORT = int(os.environ.get("ICA_PORT", "5000"))

app = Flask(__name__, static_folder=None)


def unlocked_levels() -> list[int]:
    """Levels the candidate may currently see: 1..(completed + 1), if authored."""
    completed = progress.get_completed()
    return [n for n in core.available_levels() if n <= completed + 1]


# ----- static frontend -----

@app.get("/")
def index():
    return send_from_directory(UI_DIR, "index.html")


@app.get("/<path:filename>")
def static_files(filename: str):
    return send_from_directory(UI_DIR, filename)


# ----- REST API -----

@app.get("/api/state")
def state():
    levels = unlocked_levels()
    return jsonify(
        {
            "levels": levels,
            "current": levels[-1] if levels else None,
            "completed": progress.get_completed(),
            "authored": core.available_levels(),
            "solution": core.read_solution(),
        }
    )


@app.get("/api/level/<int:n>")
def level(n: int):
    if n not in unlocked_levels():
        return jsonify({"error": "locked"}), 404
    return jsonify(
        {
            "level": n,
            "readme_md": core.read_readme(n),
            "public_test_src": core.read_public_source(n),
        }
    )


@app.get("/api/files")
def files():
    return jsonify(core.list_files(unlocked_levels()))


@app.get("/api/file/<file_id>")
def file(file_id: str):
    m = re.fullmatch(r"public-(\d+)", file_id)
    if m and int(m.group(1)) not in unlocked_levels():
        return jsonify({"error": "locked"}), 404
    content = core.read_file(file_id)
    if content is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": file_id, "content": content})


@app.post("/api/save")
def save():
    data = request.get_json(force=True)
    core.write_solution(data.get("code", ""))
    return jsonify({"ok": True})


@app.post("/api/run")
def run():
    data = request.get_json(force=True)
    target = int(data.get("level", 1))
    if target not in unlocked_levels():
        return jsonify({"error": "level locked"}), 400
    if "code" in data:
        core.write_solution(data["code"])

    unlocked_before = set(unlocked_levels())
    public = core.run_public(target)
    hidden = core.run_hidden(target)

    if public["passed"]:
        progress.set_completed(target)

    unlocked = unlocked_levels()
    newly = sorted(set(unlocked) - unlocked_before)
    return jsonify(
        {
            "public": public,
            "hidden": hidden,
            "completed": progress.get_completed(),
            "unlocked": unlocked,
            "unlocked_now": newly[-1] if newly else None,
        }
    )


if __name__ == "__main__":
    print(f"ICA IDE at http://{HOST}:{PORT}  (Ctrl+C to quit)")
    app.run(host=HOST, port=PORT, threaded=True)
