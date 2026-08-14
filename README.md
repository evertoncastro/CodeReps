# Coding Assessment Trainer

A local, single-user web IDE for practising coding assessments. Each assessment
**format** defines what a challenge looks like and how it is graded; the one shipped
today is **ICA** (Industry Coding Assessment): a business-domain Python system that
grows over 4 progressive levels, with a timer, hidden tests and a level-by-level
reveal.

---

# Part 1 — Getting started

## Requirements

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.10+ (developed on **3.12.6**) | |
| [Flask](https://flask.palletsprojects.com/) | `>=3.0` | The only third-party package. |
| SQLite | bundled with Python | Via the stdlib `sqlite3`. Nothing to install. |

The editor loads Monaco, marked and Split.js from public CDNs, so the browser needs an
internet connection the first time you open the IDE. There is no frontend build step.

Linux/macOS is recommended: the per-test time limit uses `SIGALRM`, which Windows
does not provide.

## Install and run

```bash
git clone <repo-url>
cd codesignal

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

```
Assessment IDE at http://127.0.0.1:5000  (Ctrl+C to quit)
```

Open <http://127.0.0.1:5000>.

## Taking an assessment

1. Pick a format on the landing page, then a challenge.
2. Click **New attempt** — this starts the timer and opens the IDE with the level 1
   requirements, a starter `solution.py` and the level's public tests (read-only).
3. Write your solution in the editor. It autosaves as you type.
4. Click **Run tests** (or press **Ctrl+Enter**) to run the tests for the current level.
5. When every test up to that level passes, the next level unlocks. Finishing level 4
   closes the attempt and freezes its duration.

The timer only runs while the attempt's IDE is open, so you can pause by leaving the
page. Past attempts stay listed per challenge and can be reopened (read-only) or
archived.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `ICA_HOST` | `127.0.0.1` | Server bind address. |
| `ICA_PORT` | `5000` | Server port. |
| `ICA_TEST_TIMEOUT` | `30` | Seconds before the whole test run is killed. |
| `ICA_CASE_TIMEOUT` | `5` | Time budget per individual test case. |
| `ICA_DB` | `challenges/progress.db` | SQLite file with attempts and progress. |

```bash
ICA_PORT=8080 ICA_CASE_TIMEOUT=10 python main.py
```

> This tool runs your `solution.py` in a subprocess with no sandboxing. Keep it bound
> to `127.0.0.1`.

---

# Part 2 — How it works

Diagrams of the same picture live in `COMPONENTS.md`.

## Layout

```
main.py         Flask app: pages, static assets and the JSON API
src/            challenge discovery, test execution, attempt persistence
src/formats/    one module per assessment format (ica.py today)
ui/             the frontend (plain HTML/CSS/JS, no build)
challenges/     the challenge library, partitioned by format
prompt.md       authoring spec for new ICA challenges (written in pt-BR)
```

## Formats and challenges

`challenges/` is partitioned by format, mirroring the URL: `challenges/ica/banking_system`
is served at `/ica/banking_system`. A challenge folder holds its metadata
(`challenge.json`) plus whatever its format defines — for ICA, a starter template and,
per level, a markdown statement with a public and a hidden `unittest` module. Both
formats and challenges are picked up automatically; there is no registration step
beyond listing a new format module in `src/formats/__init__.py`.

Bundled ICA challenges: `banking_system`, `cloud_storage`, `support_tickets`,
`warehouse_inventory`.

## Attempts

Every attempt ("run") is a row in SQLite with its own timer, its own progress and its
own snapshot of your code. That snapshot — not the file on disk — is the source of
truth, so attempts stay independent and finished ones are read-only, enforced on the
server. Your working `solution.py` and the database are gitignored.

## Running tests

The server writes your code to the challenge folder and runs the level's test modules
in a subprocess, with the working directory set to that folder so they can
`from solution import ...`. The harness runs each test case individually under a time
budget and reports results as JSON, so a slow solution fails the large-input tests
instead of hanging the run.

## Gating and reveal

The core counts **stages** — whatever unit of work a format defines (a level, for ICA).
Deciding whether a stage passed is the format's call. For ICA, every test from stages
1..*N* must pass — public and hidden alike, so earlier levels act as regression tests.
Public test sources are shown in the editor; hidden ones are never served to the
browser, only their results. Stage *N+1* stays locked until *N* passes, so you never see
future requirements early.
