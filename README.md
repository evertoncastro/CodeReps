# Coding Assessment Trainer

A local, single-user web IDE for practising coding assessments. Each assessment
**format** defines what a challenge looks like and how it is graded. Two ship today:

- **ICA** (Industry Coding Assessment) — a business-domain Python system that grows over
  4 progressive levels, with a timer, hidden tests and a level-by-level reveal.
- **Python Gym** — single-window drills where the tests also measure *how* you got the
  answer. The Django ORM challenge fails an N+1 solution even though its output is
  correct.

---

# Part 1 — Getting started

## Requirements

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.10+ (developed on **3.12.6**) | |
| [Flask](https://flask.palletsprojects.com/) | `>=3.0` | The app itself. |
| [Django](https://www.djangoproject.com/) | `>=5.0` | Only for the Python Gym ORM challenges. Without it that format shows as unavailable; everything else still works. |
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
2. Click **New attempt** — this starts the timer and opens the IDE with the requirements,
   a starter `solution.py` and the public tests (read-only).
3. Write your solution in the editor. It autosaves as you type.
4. Click **Run tests** (or press **Ctrl+Enter**).
5. In ICA, passing every test up to a level unlocks the next one, and finishing level 4
   closes the attempt. Python Gym challenges are a single window: passing closes the
   attempt outright.

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
src/formats/    one module per assessment format (ica.py, python_gym.py)
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

Bundled challenges: `ica/` has `banking_system`, `cloud_storage`, `support_tickets` and
`warehouse_inventory`; `python-gym/` has `django_orm_books`.

A format may need a dependency the others do not. Django powers the ORM challenges, and a
format whose imports fail is listed on the home page as unavailable — with the reason —
instead of disappearing.

## Attempts

Every attempt ("run") is a row in SQLite with its own timer, its own progress and its
own snapshot of your code. That snapshot — not the file on disk — is the source of
truth, so attempts stay independent and finished ones are read-only, enforced on the
server. Your working `solution.py` and the database are gitignored.

## Running tests

The server writes your code to the challenge folder and runs that stage's test modules in a
subprocess, with the working directory set to that folder so they can
`from solution import ...`. The harness runs each test case individually under a time
budget and reports results as JSON, so a slow solution fails the large-input tests instead
of hanging the run.

A challenge that needs a database brings its own. The Django ORM challenge configures an
in-memory SQLite instance inside that subprocess and builds the tables from your models, so
it can never reach the app's own state and leaves nothing behind.

## Gating and reveal

The core counts **stages** — whatever unit of work a format defines (a level, for ICA).
Deciding whether a stage passed is the format's call. For ICA, every test from stages
1..*N* must pass — public and hidden alike, so earlier levels act as regression tests.
Public test sources are shown in the editor; hidden ones are never served to the
browser, only their results. Stage *N+1* stays locked until *N* passes, so you never see
future requirements early.
