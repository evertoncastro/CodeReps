---
name: create-challenge
description: Author a new ICA mock-assessment challenge for this project — a business-domain coding problem with 4 progressive levels and real public/hidden unittest files, mirroring challenges/warehouse_inventory. Use when the user asks to create, add, or generate a new challenge / coding assessment / practice problem in this repo.
---

# Create a new ICA challenge

Challenges live under `challenges/<id>/`. The folder name is the challenge id and
its URL route (e.g. `challenges/warehouse_inventory` → `/warehouse_inventory`). The
app auto-discovers any folder containing `challenge.json` — **no code changes are
needed** to add a challenge.

Use `challenges/warehouse_inventory/` as the canonical example: read its
`challenge.json`, `solution_template.py`, and `level_1..4_*` files to copy the exact
conventions. The design philosophy (domains, difficulty curve) is in `prompt.md` at
the repo root — but the concrete file/format rules below reflect the current code and
win over any drift in `prompt.md`.

## What to produce

For a new challenge id `<id>`, create `challenges/<id>/` with:

```
challenges/<id>/
  challenge.json              # {"title": "...", "timebox_minutes": 60}
  solution_template.py        # starter interface stub (never shown as a file to the user)
  level_1.md                  # requirements (human-readable) + "Hidden Tests Check For"
  level_1_public_tests.py     # 5–10 visible tests (unittest)
  level_1_hidden_tests.py     # 10–20 hidden tests (unittest)
  level_2.md  level_2_public_tests.py  level_2_hidden_tests.py
  level_3.md  level_3_public_tests.py  level_3_hidden_tests.py
  level_4.md  level_4_public_tests.py  level_4_hidden_tests.py
```

Author **all 4 levels up front** — the app reveals them progressively at runtime
(a level unlocks only after the previous one's tests pass), so you do not gate
authoring. Do NOT create `solution.py` (it is per-attempt scratch, generated from
`solution_template.py` and gitignored). Do NOT create `__init__.py`.

## Design rules (see prompt.md for full spec)

- Python only; one evolving system exposed through a single class imported as
  `from solution import <Class>`. No external APIs/DB/frameworks; avoid advanced
  algorithms (DP, graphs, heavy math).
- **Exactly 4 progressive levels**, each extending the SAME interface — never rename
  or break methods from earlier levels; later levels only add methods.
  - L1: entity creation + simple ops (~10–15 min).
  - L2: more ops, validation, state transitions; builds on L1 with no redesign.
  - L3: querying / ranking / filtering / aggregation / history — exposes weak data
    modeling.
  - L4: advanced, depends on prior levels — snapshots, rollback, expiration,
    versioning, priority, analytics.
- Methods return plain values (str/int/bool/list/dict/None) — never `print`. For
  expected business-rule failures return `None`/`False`/`[]` etc.; do not raise unless
  the spec says so.
- Pick a fresh domain each time (banking, parking, file storage, orders, billing,
  delivery, ticketing, logistics, fleet, ...) — not warehouse again unless asked.

## Test rules

Each test module is a plain top-level module run with `cwd` = the challenge folder,
so it must start with:

```python
import unittest
from solution import <Class>
```

- **Public tests** (`level_N_public_tests.py`): 5–10 tests of representative examples
  and edge cases. Must FAIL against the empty template (which raises
  `NotImplementedError`).
- **Hidden tests** (`level_N_hidden_tests.py`): 10–20 tests — validation failures,
  boundary conditions, duplicates, invalid transitions, ordering. Use
  self-documenting method names (only the name shows on failure).
- **Both public and hidden gate advancement** (regression over levels 1..N). In
  `level_N.md` list only a "Hidden Tests Check For" bullet list — never the hidden code.
- **Performance test** (L3 and/or L4): add at least one hidden test with a LARGE input
  (tens of thousands of ops) so an O(n²) solution (e.g. a list where a dict is needed)
  exceeds the per-test time budget (`ICA_CASE_TIMEOUT`, default 5s, enforced via
  SIGALRM by `src/test_harness.py`) and is flagged, while a correct O(n)/O(n log n)
  solution finishes well under it. Size N with wide margin (e.g. 40000) to avoid flakiness.
- Tests run and display in **definition order**, so order the methods top-to-bottom the
  way you want them shown.

## Skeletons

`challenge.json`:
```json
{ "title": "<Human Title>", "timebox_minutes": 60 }
```

`solution_template.py` (only the Level 1 interface, stubbed):
```python
class <Class>:
    """<Domain> — implement the methods required by the current level. The SAME
    class evolves across all 4 levels; add methods without renaming/breaking earlier ones."""

    def __init__(self) -> None:
        raise NotImplementedError

    def <l1_method>(self, ...):
        """<contract: what it returns, and the failure return>."""
        raise NotImplementedError
    # ... rest of the Level 1 interface, all raising NotImplementedError
```

`level_N_public_tests.py` / `level_N_hidden_tests.py`:
```python
import unittest
from solution import <Class>


class Level<N>PublicTests(unittest.TestCase):   # or Level<N>HiddenTests
    def test_<descriptive_name>(self):
        inv = <Class>()
        self.assertEqual(inv.<method>(...), <expected>)
    # ... more tests, in the order you want them shown


if __name__ == "__main__":
    unittest.main()
```

`level_N.md`: title, prose requirements with each new method's signature and its
contract (return value + failure return), then a "## Hidden Tests Check For" bullet
list describing (not showing) the hidden checks.

## Verify before finishing (required)

Write a correct **reference solution** and confirm every level passes, in a temp copy
so you never touch the challenge's scratch `solution.py`:

```bash
cd /home/everton/dev/personal/justcode/codesignal
rm -rf /tmp/ica_verify && cp -r challenges/<id> /tmp/ica_verify
cat > /tmp/ica_verify/solution.py <<'PY'
# ... a full correct reference implementation of all 4 levels ...
PY
cd /tmp/ica_verify && PYTHONPATH=/tmp/ica_verify python3 -m unittest -q \
  level_1_public_tests level_1_hidden_tests \
  level_2_public_tests level_2_hidden_tests \
  level_3_public_tests level_3_hidden_tests \
  level_4_public_tests level_4_hidden_tests
rm -rf /tmp/ica_verify
```

Expect `OK` (0 failures). Also sanity-check that the **empty template fails** the
public tests (run the same command with `solution_template.py` copied in as
`solution.py`) — proving the tests actually gate. Do not commit the reference solution;
it is only for verification.

## After creating

The challenge appears automatically on the landing page (`/`) and at `/<id>`. If a dev
server is running, no restart is needed for new files; if you added it while the server
was down, just `python main.py`.
