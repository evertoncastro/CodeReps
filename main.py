#!/usr/bin/env python3
"""ICA mock assessment runner — runs local tests, with NO LLM.

Challenges are authored by the assistant (this session) as files under
workspace/challenge_library/. Each level (level1..level4) contains:

    levelN/README.md        level requirements
    levelN/public_test.py   public tests (unittest, `from solution import ...`)
    levelN/hidden_test.py   hidden tests (unittest)
    levelN/__init__.py      package marker

The solution evolves in a single file: challenge_library/solution.py.

Usage:
    python main.py            # run the highest available level (with regression)
    python main.py 2          # run up to level 2 (public 1..2 + hidden 2)
    python main.py --list     # list available levels
"""

import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
LIB = BASE / "workspace" / "challenge_library"
SOLUTION = LIB / "solution.py"
TIMEOUT = int(os.environ.get("ICA_TEST_TIMEOUT", "30"))


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
    if not init.exists():
        init.write_text("")


def run_module(module: str) -> tuple[bool, str]:
    """Run a unittest module with cwd=LIB so `solution` is importable."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "-v", module],
            cwd=LIB,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT: tests exceeded {TIMEOUT}s"
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def evaluate(target: int) -> bool:
    """Public tests 1..target (regression) gate; hidden of target as feedback."""
    print("\n" + "-" * 60)
    print("  PUBLIC TESTS (gate)")
    print("-" * 60)
    all_passed = True
    for lvl in range(1, target + 1):
        ensure_package(lvl)
        passed, output = run_module(f"level{lvl}.public_test")
        label = "current" if lvl == target else "regression"
        print(f"\n[Level {lvl} public — {label}] {'PASS' if passed else 'FAIL'}")
        print(output)
        all_passed = all_passed and passed

    hidden = LIB / f"level{target}" / "hidden_test.py"
    if hidden.exists():
        h_passed, h_output = run_module(f"level{target}.hidden_test")
        print("\n" + "-" * 60)
        print(f"  HIDDEN TESTS (Level {target}) — feedback, non-blocking")
        print("-" * 60)
        print("PASS" if h_passed else "FAIL")
        print(h_output)

    return all_passed


def main() -> None:
    args = sys.argv[1:]
    levels = available_levels()

    if "--list" in args:
        print("Available levels:", levels or "(none)")
        return

    if not levels:
        print(f"No levels found under {LIB}.")
        print("Ask the assistant to generate a challenge first.")
        sys.exit(1)

    if not SOLUTION.exists():
        print(f"Error: {SOLUTION} does not exist. Implement your solution there.")
        sys.exit(1)

    if args:
        try:
            target = int(args[0])
        except ValueError:
            print(f"Invalid argument: {args[0]}. Use a level number or --list.")
            sys.exit(1)
        if target not in levels:
            print(f"Level {target} not available. Available: {levels}")
            sys.exit(1)
    else:
        target = levels[-1]

    print("=" * 60)
    print(f"  ICA Runner — evaluating up to Level {target}")
    print("=" * 60)
    print(f"Solution: {SOLUTION}")

    passed = evaluate(target)
    print("\n" + "=" * 60)
    if passed:
        print(f"  Level {target}: ALL public tests PASSED.")
        if target < 4:
            print("  >> Tell the assistant to reveal the next level.")
        else:
            print("  >> Assessment complete!")
    else:
        print(f"  Level {target}: public tests FAILED. Fix and run again.")
    print("=" * 60)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
