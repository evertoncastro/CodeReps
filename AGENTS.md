# AGENTS.md

Local, single-user web IDE for practising ICA-style coding assessments (4 progressive
levels, timer, public + hidden tests). See `README.md` for user-facing setup.

**This file is the single source of truth for every coding agent.** `CLAUDE.md`,
`GEMINI.md` and `.github/copilot-instructions.md` are pointers to it — put instructions
here, never in them.

## Playbooks

Task-specific instructions live under `.agents/skills/` and are read on demand, so they
cost nothing until they are needed. Read the whole file before starting the task.

- **Authoring a new challenge** → `.agents/skills/create-challenge/SKILL.md`

(`.claude/skills/` mirrors these as stubs so Claude Code autoloads them; the file under
`.agents/skills/` is always the real one.)

## Stack

Python 3.10+ (3.12 in `.venv`), Flask as the only third-party dependency, stdlib
`sqlite3` for state. Frontend is plain HTML/CSS/JS with no build step and no
`package.json`; Monaco, marked and Split.js come from CDNs in `ui/index.html`.

## Layout

```
main.py                 Flask app: routes, API, auth-free single-user server
src/runner_core.py      challenge discovery, whitelisted file access, test execution
src/test_harness.py     subprocess: runs unittest modules -> JSON on stdout
src/runs.py             attempt persistence (timer, progress, code snapshot)
src/progress.py         legacy per-challenge progress table; superseded by runs.py
ui/                     challenges.html/js, attempts.html/js, index.html+app.js, style.css
challenges/<id>/        one challenge; folder name is the id AND the URL route
prompt.md               authoring spec for challenges (pt-BR)
.agents/skills/         canonical playbooks (see Playbooks above)
```

A challenge folder holds `challenge.json` (`title`, `timebox_minutes`),
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
curl -s localhost:5000/api/challenges
curl -s -XPOST localhost:5000/api/warehouse_inventory/runs
curl -s -XPOST localhost:5000/api/warehouse_inventory/run/1/run \
     -H 'content-type: application/json' -d '{"level":1}'
```

Set `ICA_DB=/tmp/x.db` to avoid touching real attempt history. Other env vars:
`ICA_HOST`, `ICA_PORT`, `ICA_TEST_TIMEOUT` (whole run, 30s), `ICA_CASE_TIMEOUT`
(per test case, 5s).

To run a challenge's tests without the server:

```bash
cd challenges/<id> && PYTHONPATH=. python ../../src/test_harness.py level_1_public_tests
```

## Invariants — do not break these

- **Hidden test sources are never served.** `runner_core.list_files` / `_resolve_file`
  whitelist only `solution` and `public-<n>`; `solution_template.py` is not exposed
  either. Any new file-serving route must go through that whitelist.
- **Levels are gated server-side.** Requests for a locked level's statement, file or
  test run must 404/400 (`unlocked_levels_for_run` in `main.py`). Never let the client
  decide what is unlocked.
- **Finished attempts are read-only**, enforced in `main.py` (`_reject_if_not_active`).
  Being over the timebox does NOT lock a run — the timebox is a target, not a stop.
- **A run's DB snapshot is the source of truth** for its code; `challenges/<id>/solution.py`
  on disk is a scratch file synced from the active run right before tests execute.
- **Passing level N requires all public AND hidden tests for levels 1..N.**
- **The harness contract**: `test_harness.py` prints exactly one JSON object on stdout.
  Anything else printed there corrupts the result — test/solution output is captured
  and attached per test as `output`.
- `challenges/progress.db` and `challenges/*/solution.py` are gitignored; don't commit
  them or add generated state elsewhere.

## Conventions

- Stdlib-only outside of Flask. Challenges must not use network, DBs or frameworks.
- Module docstrings explain the *why*; keep them accurate when behaviour changes.
- Backend: type hints on signatures, small functions, `abort(404)` for unknown
  challenges/runs. `runs.py` migrates its own schema in `_conn()` (`ALTER TABLE` guarded
  by `PRAGMA table_info`) — extend that pattern instead of writing migration scripts.
- Frontend: vanilla ES modules-free JS, no framework, no bundler. Match `app.js` style.

## Authoring challenges

Follow `prompt.md`: 4 levels, one evolving `solution.py`, a public interface that only
ever extends (never rename or break an existing method), 5–10 public and 10–20 hidden
tests per level, at least one large-input performance test at level 3/4 sized so an
O(n)/O(n log n) solution passes comfortably and a quadratic one blows the case budget.
Tests are top-level modules run with `cwd` at the challenge folder and start with
`from solution import ...`. Never reveal future-level requirements early.
