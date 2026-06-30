"""Run unittest modules and emit structured JSON results.

Invoked as a subprocess with cwd=challenge_library and PYTHONPATH=challenge_library
so that `solution` and the `levelN` packages are importable. Test module names
are passed as argv (e.g. "level1.public_test"). Output is a single JSON object on
stdout: {"tests": [{"name", "status", "message"}], "passed": bool}.

Statuses: "ok" | "fail" | "error" | "skip".
"""

import json
import sys
import traceback
import unittest


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


def main() -> None:
    modules = sys.argv[1:]
    loader = unittest.TestLoader()
    result = JSONResult()

    for module in modules:
        try:
            suite = loader.loadTestsFromName(module)
        except Exception:
            # Import/collection error (e.g. syntax error in solution.py).
            result.records.append(
                {"name": module, "status": "error", "message": traceback.format_exc().strip()}
            )
            continue
        suite.run(result)

    passed = bool(result.records) and all(r["status"] == "ok" for r in result.records)
    print(json.dumps({"passed": passed, "tests": result.records}))


if __name__ == "__main__":
    main()
