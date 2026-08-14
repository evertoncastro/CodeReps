# AGENTS.md

Local, single-user web IDE for practising coding assessments. An assessment **format**
(see `src/formats/`) owns what a challenge looks like and how it is graded. Two exist: ICA
(four progressive levels against one evolving `solution.py`) and python-gym (single-window
drills whose tests also measure *how* the answer was produced). See `README.md` for
user-facing setup and `COMPONENTS.md` for diagrams.

**This file is the single source of truth for every coding agent.** `CLAUDE.md`,
`GEMINI.md` and `.github/copilot-instructions.md` are pointers to it — put instructions
here, never in them.

## Playbooks

Task-specific instructions live under `.agents/skills/` and are read on demand, so they
cost nothing until they are needed. Read the whole file before starting the task.

- **Authoring a new challenge** → `.agents/skills/create-challenge/SKILL.md`
- **Refactoring** (ends with a docs pass) → `.agents/skills/refactor/SKILL.md`

(`.claude/skills/` mirrors these as stubs so Claude Code autoloads them; the file under
`.agents/skills/` is always the real one.)

## Stack

Python 3.10+ (3.12 in `.venv`), Flask for the app and stdlib `sqlite3` for state, plus
whatever a format needs (Django, for python-gym). Frontend is plain HTML/CSS/JS with no
build step and no `package.json`; Monaco, marked and Split.js come from CDNs in
`ui/index.html`.

## Layout

```
main.py                    Flask app: routing, gating, persistence. Format-agnostic.
src/runner_core.py         challenge discovery + run_modules() subprocess. Format-agnostic.
src/test_harness.py        subprocess: runs unittest modules -> JSON on stdout
src/runs.py                attempt persistence (timer, progress, code snapshot)
src/formats/__init__.py    format registry + the contract every format implements
src/formats/ica.py         ALL ICA specifics: levels, public/hidden pairs, solution.py
src/formats/python_gym.py  single-stage drills; hidden failures report the name only
ui/                        formats/challenges/attempts pages + index.html+app.js (the IDE)
challenges/<format>/<id>/  one challenge; both names are URL segments
prompt.md                  authoring spec for ICA challenges (pt-BR)
.agents/skills/            canonical playbooks (see Playbooks above)
```

The core speaks **stages** — a stage is whatever unit of work a format defines (a level
for ICA). It never learns a format's vocabulary: the format exports `STAGE_LABEL`
("Level") and the UI renders that.

**Adding a format**: write `src/formats/<format>.py` implementing the contract documented
in `src/formats/__init__.py`, add its id to `_CANDIDATES` there, and drop challenge
folders under `challenges/<format>/`. Nothing else — challenges are discovered by their
`challenge.json`, and every route already carries the format segment. A single-stage format
just returns `[1]` from `stages()`; the UI drops its tab strip on its own.

A python-gym challenge folder holds `challenge.json`, `task.md`, `solution_template.py`,
`public_tests.py`, `hidden_tests.py` and `gym_harness.py` — the last one is where the
challenge declares its own database (today an in-memory SQLite built from the candidate's
models), which is why a challenge that needs no database simply has no such file.

An ICA challenge folder holds `challenge.json` (`title`, `timebox_minutes`),
`solution_template.py`, `solution.py`, and per level `level_N.md`,
`level_N_public_tests.py`, `level_N_hidden_tests.py`. Levels are discovered by
globbing `level_*_public_tests.py` — there is no registry to update.

## Run and verify

```bash
source .venv/bin/activate
python main.py                       # http://127.0.0.1:5000
```

There is no test suite for the app itself. To verify a change, exercise the API
directly, e.g.:

```bash
curl -s localhost:5000/api/formats
curl -s localhost:5000/api/ica/challenges
curl -s -XPOST localhost:5000/api/ica/warehouse_inventory/runs
curl -s -XPOST localhost:5000/api/ica/warehouse_inventory/run/1/run \
     -H 'content-type: application/json' -d '{"stage":1}'
```

Use a spare port too (`ICA_PORT=5001`) so a server the user already has open on 5000
does not answer — and swallow your writes — instead of yours.

Set `ICA_DB=/tmp/x.db` to avoid touching real attempt history. Other env vars:
`ICA_HOST`, `ICA_PORT`, `ICA_TEST_TIMEOUT` (whole run, 30s), `ICA_CASE_TIMEOUT`
(per test case, 5s).

To run a challenge's tests without the server:

```bash
cd challenges/ica/<id> && PYTHONPATH=. python ../../../src/test_harness.py level_1_public_tests
cd challenges/python-gym/<id> && PYTHONPATH=. python ../../../src/test_harness.py public_tests
```

## Invariants — do not break these

- **A format's `read_file` is a whitelist.** ICA maps only `solution` and `public-<n>`;
  hidden tests and `solution_template.py` are unaddressable. Any new file-serving path
  must go through `module.read_file`, never build a path from client input.
- **Stages are gated server-side.** Requests for a locked stage's statement, file or
  test run must 404/400 (`unlocked_stages_for_run` in `main.py`). Never let the client
  decide what is unlocked.
- **Finished attempts are read-only**, enforced in `main.py` (`_reject_if_not_active`).
  Being over the timebox does NOT lock a run — the timebox is a target, not a stop.
- **A run's DB snapshot is the source of truth** for its code; the file the format
  materializes on disk (for ICA, `challenges/ica/<id>/solution.py`) is scratch, written
  only inside `run_stage` right before the tests execute.
- **The gate is the format's call.** `run_stage` returns `passed`; `main.py` must not
  reimplement it. For ICA that means all public AND hidden tests for stages 1..N.
- **The harness runs each test case individually** (for definition order and a per-case
  time budget), which bypasses unittest's class-level fixtures: `setUpClass` and
  `tearDownClass` never run. Put per-class setup in `setUp` behind an idempotent guard,
  the way `gym_harness.py` creates its tables.
- **How much of a hidden failure reaches the browser is the format's call.** python-gym
  strips `message`/`output` from hidden records (a traceback prints the failing source
  line, handing over the fixtures); ICA does not, and its hidden tracebacks are visible.
- **The harness contract**: `test_harness.py` prints exactly one JSON object on stdout.
  Anything else printed there corrupts the result — test/solution output is captured
  and attached per test as `output`.
- `challenges/progress.db` and `challenges/*/*/solution.py` are gitignored; don't commit
  them or add generated state elsewhere.

## Conventions

- The core (`main.py`, `runner_core.py`, `runs.py`, `test_harness.py`) is stdlib + Flask.
  A **format** may declare its own dependency — python-gym needs Django — and the registry
  lists it as unavailable, with the reason, when the import fails. ICA challenges remain
  stdlib-only: no network, DBs or frameworks.
- Module docstrings explain the *why*; keep them accurate when behaviour changes.
- Backend: type hints on signatures, small functions, `abort(404)` for unknown
  formats/challenges/runs. Format modules take `cdir` (the challenge directory) and
  never learn how the library is laid out. `runs.py` migrates its own schema in `_conn()` (`ALTER TABLE` guarded
  by `PRAGMA table_info`) — extend that pattern instead of writing migration scripts.
- Frontend: vanilla ES modules-free JS, no framework, no bundler. Match `app.js` style.

## Authoring ICA challenges

Follow `prompt.md` (challenges go under `challenges/ica/`): 4 levels, one evolving `solution.py`, a public interface that only
ever extends (never rename or break an existing method), 5–10 public and 10–20 hidden
tests per level, at least one large-input performance test at level 3/4 sized so an
O(n)/O(n log n) solution passes comfortably and a quadratic one blows the case budget.
Tests are top-level modules run with `cwd` at the challenge folder and start with
`from solution import ...`. Never reveal future-level requirements early.
