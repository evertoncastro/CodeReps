"""Run unittest modules and emit structured JSON results.

Invoked as a subprocess with cwd=<challenge dir> and PYTHONPATH=<challenge dir>
so that `solution` and the level test modules are importable. Test module names
are passed as argv (e.g. "level_1_public_tests"). Output is a single JSON object
on stdout: {"tests": [{"name", "status", "message"}], "passed": bool}.

Each individual test runs under a wall-clock budget (ICA_CASE_TIMEOUT seconds,
default 5) enforced with SIGALRM. A test that exceeds it is reported as an error
("time budget exceeded") — this is how slow solutions (e.g. quadratic algorithms
on the large-input performance tests) get flagged, without killing the whole run.

Statuses: "ok" | "fail" | "error" | "skip".
"""

import json
import os
import signal
import sys
import traceback
import unittest

CASE_TIMEOUT = float(os.environ.get("ICA_CASE_TIMEOUT", "5"))
_USE_ALARM = hasattr(signal, "SIGALRM")


class TimeBudgetExceeded(Exception):
    pass


def _on_alarm(signum, frame):
    raise TimeBudgetExceeded(
        f"time budget exceeded ({CASE_TIMEOUT:g}s) — solution too slow "
        "(e.g. a quadratic algorithm on a large input)"
    )


class JSONResult(unittest.TestResult):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict] = []

    def addSuccess(self, test) -> None:
        self.records.append({"name": test.id(), "status": "ok"})

    def addFailure(self, test, err) -> None:
        self.records.append(
            {"name": test.id(), "status": "fail", "message": self._fmt(err)}
        )

    def addError(self, test, err) -> None:
        self.records.append(
            {"name": test.id(), "status": "error", "message": self._fmt(err)}
        )

    def addSkip(self, test, reason) -> None:
        self.records.append({"name": test.id(), "status": "skip", "message": reason})

    @staticmethod
    def _fmt(err) -> str:
        return "".join(traceback.format_exception(*err)).strip()


def _iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


def main() -> None:
    modules = sys.argv[1:]
    loader = unittest.TestLoader()
    result = JSONResult()

    if _USE_ALARM:
        signal.signal(signal.SIGALRM, _on_alarm)

    for module in modules:
        try:
            suite = loader.loadTestsFromName(module)
        except Exception:
            result.records.append(
                {"name": module, "status": "error", "message": traceback.format_exc().strip()}
            )
            continue

        for test in _iter_tests(suite):
            if _USE_ALARM:
                signal.setitimer(signal.ITIMER_REAL, CASE_TIMEOUT)
            try:
                test(result)  # runs the single test, updating `result`
            finally:
                if _USE_ALARM:
                    signal.setitimer(signal.ITIMER_REAL, 0)

    passed = bool(result.records) and all(r["status"] == "ok" for r in result.records)
    print(json.dumps({"passed": passed, "tests": result.records}))


if __name__ == "__main__":
    main()
