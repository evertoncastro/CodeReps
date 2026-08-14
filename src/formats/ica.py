"""The ICA mock assessment format.

One evolving `solution.py`, four progressive levels, each with a public and a
hidden unittest module. A level is unlocked only after every test of every
earlier level still passes, so bad early design hurts later.

A challenge folder looks like:

    challenge.json                {"title", "timebox_minutes"}
    solution_template.py          starter code (never served to the candidate)
    solution.py                   the candidate's evolving solution
    level_N.md                    requirements for level N
    level_N_public_tests.py       public tests (shown read-only)
    level_N_hidden_tests.py       hidden tests (results only, never the source)

Every function takes the challenge directory, so this module never learns how
the library is laid out. See src/formats/__init__.py for the contract.
"""

import re
from pathlib import Path

import runner_core as core

ID = "ica"
TITLE = "ICA Mock Assessment"
DESCRIPTION = (
    "Four progressive levels against one evolving class, on a timebox. "
    "Public and hidden tests must both pass to unlock the next level."
)
STAGE_LABEL = "Level"

_PUBLIC_FILE_RE = re.compile(r"^level_(\d+)_public_tests\.py$")
_PUBLIC_ID_RE = re.compile(r"^public-(\d+)$")


def stages(cdir: Path) -> list[int]:
    """Authored levels, discovered from the public test files."""
    if not cdir.is_dir():
        return []
    found = []
    for p in cdir.glob("level_*_public_tests.py"):
        m = _PUBLIC_FILE_RE.match(p.name)
        if m:
            found.append(int(m.group(1)))
    return sorted(found)


def stage_doc(cdir: Path, stage: int) -> str:
    """The level's requirements, as markdown."""
    f = cdir / f"level_{stage}.md"
    return f.read_text() if f.exists() else ""


def files(cdir: Path, unlocked: list[int]) -> list[dict]:
    """Files exposed in the UI explorer.

    Only solution.py (editable) and the public tests of unlocked levels
    (read-only) are listed. Hidden test sources are NEVER exposed.
    """
    out = [{"id": "solution", "label": "solution.py", "editable": True}]
    for n in unlocked:
        if (cdir / f"level_{n}_public_tests.py").exists():
            out.append(
                {"id": f"public-{n}", "label": f"level_{n}_public_tests.py", "editable": False}
            )
    return out


def stage_of_file(file_id: str) -> int | None:
    """The level a file id belongs to, or None when it is not level-gated."""
    m = _PUBLIC_ID_RE.match(file_id or "")
    return int(m.group(1)) if m else None


def read_file(cdir: Path, file_id: str) -> str | None:
    """Content of a whitelisted file id. Anything else is unaddressable."""
    if file_id == "solution":
        p = cdir / "solution.py"
    elif (n := stage_of_file(file_id)) is not None:
        p = cdir / f"level_{n}_public_tests.py"
    else:
        return None
    return p.read_text() if p.exists() else None


def new_solution(cdir: Path) -> str:
    """Starter code for a fresh attempt (the template is never served as a file)."""
    p = cdir / "solution_template.py"
    return p.read_text() if p.exists() else ""


def run_stage(cdir: Path, target: int, code: str) -> dict:
    """Grade `code` against levels 1..target (regression).

    The gate is deliberately strict, like the real assessment: every public AND
    every hidden test up to the target level must pass to advance.
    """
    (cdir / "solution.py").write_text(code)

    public = _run(cdir, [f"level_{n}_public_tests" for n in range(1, target + 1)])
    hidden_modules = [
        f"level_{n}_hidden_tests"
        for n in range(1, target + 1)
        if (cdir / f"level_{n}_hidden_tests.py").exists()
    ]
    if hidden_modules:
        hidden = _run(cdir, hidden_modules)
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
