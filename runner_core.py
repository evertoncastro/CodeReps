"""Shared execution core for the ICA mock assessment.

Both the CLI (main.py) and the web UI (ui.py) import this module so that tests
run the exact same way against the same files on disk.

The challenges/ directory is a library of challenges, one folder each:

    challenges/
        progress.db                       progress + timer state (gitignored)
        warehouse_inventory/              one challenge
            challenge.json                {"title", "timebox_minutes"}
            solution.py                   evolving solution (the candidate edits)
            level_N.md                    requirements for level N
            level_N_public_tests.py       public tests (gate)
            level_N_hidden_tests.py       hidden tests (feedback)

Test modules are plain top-level modules (no packages); they import the
candidate's code via `from solution import ...` and run with cwd set to the
challenge folder so `solution` and the module names resolve.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
LIBRARY = BASE / "challenges"
HARNESS = BASE / "test_harness.py"
TIMEOUT = int(os.environ.get("ICA_TEST_TIMEOUT", "30"))

_PUBLIC_FILE_RE = re.compile(r"^level_(\d+)_public_tests\.py$")
_TEST_NAME_RE = re.compile(r"^level_(\d+)_")
_CID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def challenge_dir(challenge: str) -> Path:
    return LIBRARY / challenge


def is_challenge(challenge: str) -> bool:
    """Whether `challenge` is a valid, existing challenge id (no traversal)."""
    if not challenge or not _CID_RE.match(challenge):
        return False
    return (challenge_dir(challenge) / "challenge.json").exists()


def read_challenge_meta(challenge: str) -> dict:
    """Challenge metadata (title, timebox). Falls back to sensible defaults."""
    meta = {"title": challenge, "timebox_minutes": 60}
    f = challenge_dir(challenge) / "challenge.json"
    if f.exists():
        try:
            meta.update(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    return meta


def list_challenges() -> list[dict]:
    """All challenges in the library, sorted by id."""
    out = []
    if not LIBRARY.is_dir():
        return out
    for d in sorted(LIBRARY.iterdir()):
        if d.is_dir() and (d / "challenge.json").exists():
            meta = read_challenge_meta(d.name)
            out.append(
                {
                    "id": d.name,
                    "title": meta.get("title"),
                    "timebox_minutes": meta.get("timebox_minutes"),
                    "levels": len(available_levels(d.name)),
                }
            )
    return out


def available_levels(challenge: str) -> list[int]:
    cdir = challenge_dir(challenge)
    if not cdir.is_dir():
        return []
    levels = []
    for p in cdir.glob("level_*_public_tests.py"):
        m = _PUBLIC_FILE_RE.match(p.name)
        if m:
            levels.append(int(m.group(1)))
    return sorted(levels)


def level_of(test_name: str) -> int | None:
    m = _TEST_NAME_RE.match(test_name)
    return int(m.group(1)) if m else None


def solution_path(challenge: str) -> Path:
    return challenge_dir(challenge) / "solution.py"


def read_solution(challenge: str) -> str:
    p = solution_path(challenge)
    return p.read_text() if p.exists() else ""


def write_solution(challenge: str, code: str) -> None:
    challenge_dir(challenge).mkdir(parents=True, exist_ok=True)
    solution_path(challenge).write_text(code)


def read_readme(challenge: str, level: int) -> str:
    f = challenge_dir(challenge) / f"level_{level}.md"
    return f.read_text() if f.exists() else ""


def read_public_source(challenge: str, level: int) -> str:
    f = challenge_dir(challenge) / f"level_{level}_public_tests.py"
    return f.read_text() if f.exists() else ""


def list_files(challenge: str, levels: list[int] | None = None) -> list[dict]:
    """Files exposed in the UI explorer.

    Only solution.py (editable) and each level's public tests (read-only) are
    listed. Hidden test sources are NEVER exposed. Pass `levels` to restrict to
    the currently unlocked levels (defaults to all authored levels).
    """
    if levels is None:
        levels = available_levels(challenge)
    files = [{"id": "solution", "label": "solution.py", "editable": True}]
    for n in levels:
        if (challenge_dir(challenge) / f"level_{n}_public_tests.py").exists():
            files.append(
                {"id": f"public-{n}", "label": f"level_{n}_public_tests.py", "editable": False}
            )
    return files


def _resolve_file(challenge: str, file_id: str) -> Path | None:
    """Map a whitelisted file id to a path. Returns None for anything else."""
    if file_id == "solution":
        return solution_path(challenge)
    m = re.fullmatch(r"public-(\d+)", file_id or "")
    if m:
        return challenge_dir(challenge) / f"level_{m.group(1)}_public_tests.py"
    return None


def read_file(challenge: str, file_id: str) -> str | None:
    p = _resolve_file(challenge, file_id)
    if p is None or not p.exists():
        return None
    return p.read_text()


def _run_modules(challenge: str, modules: list[str]) -> dict:
    """Run unittest modules via the harness; return {passed, tests:[...]}."""
    if not modules:
        return {"passed": False, "tests": []}
    cdir = challenge_dir(challenge)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(cdir) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            [sys.executable, str(HARNESS), *modules],
            cwd=cdir,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "tests": [{"name": "timeout", "status": "error",
                       "message": f"tests exceeded {TIMEOUT}s"}],
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "passed": False,
            "tests": [{"name": "harness", "status": "error",
                       "message": (proc.stdout + proc.stderr).strip()}],
        }


def run_public(challenge: str, target: int) -> dict:
    """Run public tests for levels 1..target (regression). Gate = all pass."""
    modules = [f"level_{lvl}_public_tests" for lvl in range(1, target + 1)]
    result = _run_modules(challenge, modules)
    for t in result["tests"]:
        t["level"] = level_of(t["name"])
        t["short"] = t["name"].rsplit(".", 1)[-1]
    return result


def run_hidden(challenge: str, level: int) -> dict:
    """Run hidden tests for a single level (feedback, non-blocking)."""
    if not (challenge_dir(challenge) / f"level_{level}_hidden_tests.py").exists():
        return {"passed": True, "tests": [], "passed_count": 0, "total": 0}
    result = _run_modules(challenge, [f"level_{level}_hidden_tests"])
    for t in result["tests"]:
        t["short"] = t["name"].rsplit(".", 1)[-1]
    result["passed_count"] = sum(1 for t in result["tests"] if t["status"] == "ok")
    result["total"] = len(result["tests"])
    return result
