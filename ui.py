#!/usr/bin/env python3
"""Local web IDE for the ICA mock assessment (single user, runs on your machine).

    python ui.py            # serve at http://localhost:5000

Provides a REST API to read challenge state, save solution.py, and run tests
(structured pass/fail), reusing runner_core (same execution path as the CLI).

Hidden test sources are never exposed: only the README and the public test
source are served. Tests run in a subprocess via runner_core.
"""

import os

from flask import Flask, jsonify, request, send_from_directory

import runner_core as core

UI_DIR = core.BASE / "ui"
HOST = os.environ.get("ICA_HOST", "127.0.0.1")
PORT = int(os.environ.get("ICA_PORT", "5000"))

app = Flask(__name__, static_folder=None)


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
    levels = core.available_levels()
    return jsonify(
        {
            "levels": levels,
            "current": levels[-1] if levels else None,
            "solution": core.read_solution(),
        }
    )


@app.get("/api/level/<int:n>")
def level(n: int):
    return jsonify(
        {
            "level": n,
            "readme_md": core.read_readme(n),
            "public_test_src": core.read_public_source(n),
        }
    )


@app.get("/api/files")
def files():
    return jsonify(core.list_files())


@app.get("/api/file/<file_id>")
def file(file_id: str):
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
    if "code" in data:
        core.write_solution(data["code"])
    return jsonify(
        {
            "public": core.run_public(target),
            "hidden": core.run_hidden(target),
        }
    )


if __name__ == "__main__":
    print(f"ICA IDE at http://{HOST}:{PORT}  (Ctrl+C to quit)")
    app.run(host=HOST, port=PORT, threaded=True)
