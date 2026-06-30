"""Shared execution core for the ICA mock assessment.

Both the CLI (main.py) and the web UI (ui.py) import this module so that tests
run the exact same way against the same files on disk.

Flat layout (one challenge at a time), all under workspace/challenge_library/:
    solution.py                 evolving solution (the candidate edits this)
    level_N.md                  requirements for level N
    level_N_public_tests.py     public tests (gate)
    level_N_hidden_tests.py     hidden tests (feedback)

Test modules are plain top-level modules (no packages); they import the
candidate's code via `from solution import ...` and are run with
cwd=challenge_library so `solution` and the module names resolve.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
LIB = BASE / "workspace" / "challenge_library"
SOLUTION = LIB / "solution.py"
HARNESS = BASE / "test_harness.py"
TIMEOUT = int(os.environ.get("ICA_TEST_TIMEOUT", "30"))

_PUBLIC_FILE_RE = re.compile(r"^level_(\d+)_public_tests\.py$")
_TEST_NAME_RE = re.compile(r"^level_(\d+)_")


def available_levels() -> list[int]:
    if not LIB.is_dir():
        return []
    levels = []
    for p in LIB.glob("level_*_public_tests.py"):
        m = _PUBLIC_FILE_RE.match(p.name)
        if m:
            levels.append(int(m.group(1)))
    return sorted(levels)


def level_of(test_name: str) -> int | None:
    m = _TEST_NAME_RE.match(test_name)
    return int(m.group(1)) if m else None


def read_solution() -> str:
    return SOLUTION.read_text() if SOLUTION.exists() else ""


def write_solution(code: str) -> None:
    LIB.mkdir(parents=True, exist_ok=True)
    SOLUTION.write_text(code)


def read_readme(level: int) -> str:
    f = LIB / f"level_{level}.md"
    return f.read_text() if f.exists() else ""


def read_public_source(level: int) -> str:
    f = LIB / f"level_{level}_public_tests.py"
    return f.read_text() if f.exists() else ""


def list_files(levels: list[int] | None = None) -> list[dict]:
    """Files exposed in the UI explorer.

    Only solution.py (editable) and each level's public tests (read-only) are
    listed. Hidden test sources are NEVER exposed. Pass `levels` to restrict to
    the currently unlocked levels (defaults to all authored levels).
    """
    if levels is None:
        levels = available_levels()
    files = [{"id": "solution", "label": "solution.py", "editable": True}]
    for n in levels:
        if (LIB / f"level_{n}_public_tests.py").exists():
            files.append(
                {"id": f"public-{n}", "label": f"level_{n}_public_tests.py", "editable": False}
            )
    return files


def _resolve_file(file_id: str) -> Path | None:
    """Map a whitelisted file id to a path. Returns None for anything else."""
    if file_id == "solution":
        return SOLUTION
    m = re.fullmatch(r"public-(\d+)", file_id or "")
    if m:
        return LIB / f"level_{m.group(1)}_public_tests.py"
    return None


def read_file(file_id: str) -> str | None:
    p = _resolve_file(file_id)
    if p is None or not p.exists():
        return None
    return p.read_text()


def _run_modules(modules: list[str]) -> dict:
    """Run unittest modules via the harness; return {passed, tests:[...]}."""
    if not modules:
        return {"passed": False, "tests": []}
    env = dict(os.environ)
    env["PYTHONPATH"] = str(LIB) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            [sys.executable, str(HARNESS), *modules],
            cwd=LIB,
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


def run_public(target: int) -> dict:
    """Run public tests for levels 1..target (regression). Gate = all pass."""
    modules = [f"level_{lvl}_public_tests" for lvl in range(1, target + 1)]
    result = _run_modules(modules)
    for t in result["tests"]:
        t["level"] = level_of(t["name"])
        t["short"] = t["name"].rsplit(".", 1)[-1]
    return result


def run_hidden(level: int) -> dict:
    """Run hidden tests for a single level (feedback, non-blocking)."""
    if not (LIB / f"level_{level}_hidden_tests.py").exists():
        return {"passed": True, "tests": [], "passed_count": 0, "total": 0}
    result = _run_modules([f"level_{level}_hidden_tests"])
    for t in result["tests"]:
        t["short"] = t["name"].rsplit(".", 1)[-1]
    result["passed_count"] = sum(1 for t in result["tests"] if t["status"] == "ok")
    result["total"] = len(result["tests"])
    return result
