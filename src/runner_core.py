"""Format-agnostic core: challenge discovery and test execution.

The challenges/ directory is partitioned by assessment format; a challenge is a
folder holding a challenge.json, and its name is both the challenge id and the
last URL segment:

    challenges/
        progress.db                       attempts + timer state (gitignored)
        ica/                              one assessment format
            warehouse_inventory/          one challenge
                challenge.json            {"title", "timebox_minutes"}
                ...                       whatever else the format defines

What lives inside a challenge folder is the format's business (see
src/formats/), not this module's. Here we only find challenges, read their
metadata, and run test modules in a subprocess.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent
ROOT = SRC_DIR.parent  # project root (contains challenges/, ui/, main.py)
LIBRARY = ROOT / "challenges"
HARNESS = SRC_DIR / "test_harness.py"
TIMEOUT = int(os.environ.get("ICA_TEST_TIMEOUT", "30"))

_CID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def format_dir(fmt: str) -> Path:
    return LIBRARY / fmt


def challenge_dir(fmt: str, challenge: str) -> Path:
    return LIBRARY / fmt / challenge


def is_challenge(fmt: str, challenge: str) -> bool:
    """Whether `challenge` is a valid, existing challenge id (no traversal)."""
    if not challenge or not _CID_RE.match(challenge) or not _CID_RE.match(fmt or ""):
        return False
    return (challenge_dir(fmt, challenge) / "challenge.json").exists()


def read_challenge_meta(fmt: str, challenge: str) -> dict:
    """Challenge metadata (title, timebox). Falls back to sensible defaults."""
    meta = {"title": challenge, "timebox_minutes": 60}
    f = challenge_dir(fmt, challenge) / "challenge.json"
    if f.exists():
        try:
            meta.update(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    return meta


def list_challenges(fmt: str) -> list[dict]:
    """All challenges of one format, sorted by id (stage counts come from the format)."""
    out = []
    fdir = format_dir(fmt)
    if not fdir.is_dir():
        return out
    for d in sorted(fdir.iterdir()):
        if d.is_dir() and (d / "challenge.json").exists():
            meta = read_challenge_meta(fmt, d.name)
            out.append(
                {
                    "id": d.name,
                    "title": meta.get("title"),
                    "timebox_minutes": meta.get("timebox_minutes"),
                }
            )
    return out


def run_modules(cdir: Path, modules: list[str]) -> dict:
    """Run unittest modules in `cdir` via the harness; return {passed, tests:[...]}.

    Format-agnostic: the caller decides which module names to run. Each test
    gets its own time budget inside the harness (ICA_CASE_TIMEOUT)."""
    if not modules:
        return {"passed": False, "tests": []}
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
