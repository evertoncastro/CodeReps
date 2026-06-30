#!/usr/bin/env python3
"""ICA mock assessment runner (CLI) — runs local tests, with NO LLM.

Challenges live under challenges/<name>/ (see runner_core). The solution evolves
in challenges/<name>/solution.py.

Usage:
    python main.py                       # if exactly one challenge, run its top level
    python main.py <challenge>           # run that challenge's highest level
    python main.py <challenge> 2         # run up to level 2 (public 1..2 + hidden 2)
    python main.py --list                # list challenges
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
    challenges = [c["id"] for c in core.list_challenges()]

    if "--list" in args:
        print("Challenges:", challenges or "(none)")
        return

    if not challenges:
        print(f"No challenges found under {core.LIBRARY}.")
        sys.exit(1)

    # Optional first arg = challenge id.
    if args and args[0] in challenges:
        challenge = args.pop(0)
    elif len(challenges) == 1:
        challenge = challenges[0]
    else:
        print(f"Specify a challenge. Available: {challenges}")
        sys.exit(1)

    levels = core.available_levels(challenge)
    if not levels:
        print(f"No levels found for challenge '{challenge}'.")
        sys.exit(1)

    if args:
        try:
            target = int(args[0])
        except ValueError:
            print(f"Invalid level: {args[0]}. Use a level number or --list.")
            sys.exit(1)
        if target not in levels:
            print(f"Level {target} not available. Available: {levels}")
            sys.exit(1)
    else:
        target = levels[-1]

    print("=" * 60)
    print(f"  ICA Runner — {challenge} — up to Level {target}")
    print("=" * 60)
    print(f"Solution: {core.solution_path(challenge)}")

    print("\n" + "-" * 60)
    print(f"  PUBLIC TESTS (gate: levels 1..{target})")
    print("-" * 60)
    public = core.run_public(challenge, target)
    _print_tests(public["tests"])

    hidden = core.run_hidden(challenge, target)
    if hidden["total"]:
        print("\n" + "-" * 60)
        print(f"  HIDDEN TESTS (Level {target}) — feedback, non-blocking")
        print("-" * 60)
        print(f"  {hidden['passed_count']}/{hidden['total']} passed")
        _print_tests([t for t in hidden["tests"] if t["status"] != "ok"])

    print("\n" + "=" * 60)
    if public["passed"]:
        print(f"  Level {target}: ALL public tests PASSED.")
    else:
        print(f"  Level {target}: public tests FAILED. Fix and run again.")
    print("=" * 60)
    sys.exit(0 if public["passed"] else 1)


if __name__ == "__main__":
    main()
