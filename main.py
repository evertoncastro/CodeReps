#!/usr/bin/env python3
"""ICA mock assessment runner (CLI) — runs local tests, with NO LLM.

Challenges are authored by the assistant (this session) as files under
workspace/challenge_library/. The solution evolves in a single file:
challenge_library/solution.py. See runner_core for the on-disk layout.

Usage:
    python main.py            # run the highest available level (with regression)
    python main.py 2          # run up to level 2 (public 1..2 + hidden 2)
    python main.py --list     # list available levels
"""

import sys

import runner_core as core


def _print_tests(tests: list[dict]) -> None:
    for t in tests:
        mark = {"ok": "PASS", "fail": "FAIL", "error": "ERROR", "skip": "SKIP"}.get(
            t["status"], t["status"].upper()
        )
        print(f"  [{mark}] {t.get('short', t['name'])}")
        if t.get("message") and t["status"] in ("fail", "error"):
            for line in t["message"].splitlines():
                print(f"        {line}")


def main() -> None:
    args = sys.argv[1:]
    levels = core.available_levels()

    if "--list" in args:
        print("Available levels:", levels or "(none)")
        return

    if not levels:
        print(f"No levels found under {core.LIB}.")
        print("Ask the assistant to generate a challenge first.")
        sys.exit(1)

    if not core.SOLUTION.exists():
        print(f"Error: {core.SOLUTION} does not exist. Implement your solution there.")
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
    print(f"Solution: {core.SOLUTION}")

    print("\n" + "-" * 60)
    print("  PUBLIC TESTS (gate: levels 1.." + str(target) + ")")
    print("-" * 60)
    public = core.run_public(target)
    _print_tests(public["tests"])

    hidden = core.run_hidden(target)
    if hidden["total"]:
        print("\n" + "-" * 60)
        print(f"  HIDDEN TESTS (Level {target}) — feedback, non-blocking")
        print("-" * 60)
        print(f"  {hidden['passed_count']}/{hidden['total']} passed")
        _print_tests([t for t in hidden["tests"] if t["status"] != "ok"])

    print("\n" + "=" * 60)
    if public["passed"]:
        print(f"  Level {target}: ALL public tests PASSED.")
        if target < 4:
            print("  >> Tell the assistant to reveal the next level.")
        else:
            print("  >> Assessment complete!")
    else:
        print(f"  Level {target}: public tests FAILED. Fix and run again.")
    print("=" * 60)
    sys.exit(0 if public["passed"] else 1)


if __name__ == "__main__":
    main()
