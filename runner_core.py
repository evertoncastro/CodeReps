"""Shared execution core for the ICA mock assessment.

Both the CLI (main.py) and the web UI (ui.py) import this module so that tests
run the exact same way against the same files on disk.

Layout (one challenge at a time):
    workspace/challenge_library/
        solution.py            evolving solution (the candidate edits this)
        levelN/README.md       requirements
        levelN/public_test.py  public tests (gate)
        levelN/hidden_test.py  hidden tests (feedback)
        levelN/__init__.py     package marker
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

_LEVEL_RE = re.compile(r"^level(\d+)")


def available_levels() -> list[int]:
    if not LIB.is_dir():
        return []
    levels = []
    for p in LIB.glob("level*"):
        suffix = p.name[len("level"):]
        if p.is_dir() and suffix.isdigit():
            levels.append(int(suffix))
    return sorted(levels)


def ensure_package(level: int) -> None:
    init = LIB / f"level{level}" / "__init__.py"
    if init.parent.is_dir() and not init.exists():
        init.write_text("")


def level_of(test_name: str) -> int | None:
    m = _LEVEL_RE.match(test_name)
    return int(m.group(1)) if m else None


def read_solution() -> str:
    return SOLUTION.read_text() if SOLUTION.exists() else ""


def write_solution(code: str) -> None:
    LIB.mkdir(parents=True, exist_ok=True)
    SOLUTION.write_text(code)


def read_readme(level: int) -> str:
    f = LIB / f"level{level}" / "README.md"
    return f.read_text() if f.exists() else ""


def read_public_source(level: int) -> str:
    f = LIB / f"level{level}" / "public_test.py"
    return f.read_text() if f.exists() else ""


def list_files(levels: list[int] | None = None) -> list[dict]:
    """Files exposed in the UI file explorer.

    Only solution.py (editable) and each level's public_test.py (read-only) are
    listed. Hidden test sources are NEVER exposed. Pass `levels` to restrict to
    the currently unlocked levels (defaults to all authored levels).
    """
    if levels is None:
        levels = available_levels()
    files = [{"id": "solution", "label": "solution.py", "editable": True}]
    for n in levels:
        if (LIB / f"level{n}" / "public_test.py").exists():
            files.append(
                {"id": f"public-{n}", "label": f"level{n}/public_test.py", "editable": False}
            )
    return files


def _resolve_file(file_id: str) -> Path | None:
    """Map a whitelisted file id to a path. Returns None for anything else."""
    if file_id == "solution":
        return SOLUTION
    m = re.fullmatch(r"public-(\d+)", file_id or "")
    if m:
        return LIB / f"level{m.group(1)}" / "public_test.py"
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
    for lvl in range(1, target + 1):
        ensure_package(lvl)
    modules = [f"level{lvl}.public_test" for lvl in range(1, target + 1)]
    result = _run_modules(modules)
    for t in result["tests"]:
        t["level"] = level_of(t["name"])
        t["short"] = t["name"].rsplit(".", 1)[-1]
    return result


def run_hidden(level: int) -> dict:
    """Run hidden tests for a single level (feedback, non-blocking)."""
    hidden = LIB / f"level{level}" / "hidden_test.py"
    if not hidden.exists():
        return {"passed": True, "tests": [], "passed_count": 0, "total": 0}
    ensure_package(level)
    result = _run_modules([f"level{level}.hidden_test"])
    for t in result["tests"]:
        t["short"] = t["name"].rsplit(".", 1)[-1]
    result["passed_count"] = sum(1 for t in result["tests"] if t["status"] == "ok")
    result["total"] = len(result["tests"])
    return result
