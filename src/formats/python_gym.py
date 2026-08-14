"""The python-gym format: single-window drills against a real library.

One `solution.py`, one statement, one shot — there are no progressive levels, so
`stages()` returns a single stage and nothing is gated. What separates it from
ICA is the grading signal: the tests measure *how* the answer was produced (for
the Django challenges, how many SQL queries it cost), not only what it returned.

A challenge folder looks like:

    challenge.json          {"title", "timebox_minutes"}
    task.md                 the statement
    solution_template.py    starter code (never served as a file)
    solution.py             the candidate's code
    gym_harness.py          test-time setup + shared TestCase (served read-only)
    public_tests.py         public tests (shown read-only)
    hidden_tests.py         hidden tests (names + status only, never the source)

`gym_harness.py` is deliberately readable: it is where the challenge declares its
own database, so the candidate can see what they are working against. It is also
why a challenge needing no database simply has no such file.

Unlike ICA, hidden failures report the METHOD NAME ONLY — see run_stage.

Django is imported at module scope on purpose: when it is missing the format
registry catches the ImportError and lists the format as unavailable, instead of
every attempt failing at test time.
"""

from pathlib import Path

import django  # noqa: F401  — presence check; see the module docstring

import runner_core as core

ID = "python-gym"
TITLE = "Python Gym"
DESCRIPTION = (
    "Single-window drills. The tests check your results AND how you got them — "
    "an N+1 query solution fails even when every value is right."
)
STAGE_LABEL = "Exercise"

_STAGE = 1

# file id -> filename. This mapping IS the whitelist: hidden_tests.py and
# solution_template.py are absent from it, so they are unaddressable.
_FILES = {
    "solution": "solution.py",
    "public": "public_tests.py",
    "harness": "gym_harness.py",
}


def stages(cdir: Path) -> list[int]:
    """A single stage, present once the challenge has public tests."""
    return [_STAGE] if (cdir / "public_tests.py").exists() else []


def stage_doc(cdir: Path, stage: int) -> str:
    f = cdir / "task.md"
    return f.read_text() if f.exists() else ""


def files(cdir: Path, unlocked: list[int]) -> list[dict]:
    """solution.py (editable) plus the public tests and the harness (read-only)."""
    out = [{"id": "solution", "label": "solution.py", "editable": True}]
    for file_id in ("public", "harness"):
        if (cdir / _FILES[file_id]).exists():
            out.append({"id": file_id, "label": _FILES[file_id], "editable": False})
    return out


def stage_of_file(file_id: str) -> int | None:
    """Nothing is stage-gated — there is only one stage."""
    return None


def read_file(cdir: Path, file_id: str) -> str | None:
    """Content of a whitelisted file id. Anything else is unaddressable."""
    name = _FILES.get(file_id or "")
    if name is None:
        return None
    p = cdir / name
    return p.read_text() if p.exists() else None


def new_solution(cdir: Path) -> str:
    """Starter code for a fresh attempt (the template is never served as a file)."""
    p = cdir / "solution_template.py"
    return p.read_text() if p.exists() else ""


def run_stage(cdir: Path, target: int, code: str) -> dict:
    """Grade `code`: every public AND every hidden test must pass."""
    (cdir / "solution.py").write_text(code)

    public = _run(cdir, ["public_tests"])
    if (cdir / "hidden_tests.py").exists():
        hidden = _run(cdir, ["hidden_tests"])
        for t in hidden["tests"]:
            # Name and status only. A traceback prints the failing source line,
            # which would hand over both the fixtures and the expected values —
            # and those fixtures are most of the assessment.
            t.pop("message", None)
            t.pop("output", None)
        hidden["passed_count"] = sum(1 for t in hidden["tests"] if t["status"] == "ok")
        hidden["total"] = len(hidden["tests"])
    else:
        hidden = {"passed": True, "tests": [], "passed_count": 0, "total": 0}

    return {
        "passed": public["passed"] and hidden["passed"],
        "public": public,
        "hidden": hidden,
    }


def _run(cdir: Path, modules: list[str]) -> dict:
    result = core.run_modules(cdir, modules)
    for t in result["tests"]:
        t["short"] = t["name"].rsplit(".", 1)[-1]
    return result
