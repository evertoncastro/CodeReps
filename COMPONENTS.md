# Components

How the pieces fit together. The core is format-agnostic; assessment formats (ICA and
python-gym today) plug into it. See `README.md` for setup and `AGENTS.md` for working
rules.

## System overview

```mermaid
graph TB
    subgraph browser["Browser"]
        pages["Pages<br/>formats · challenges · attempts · IDE"]
        appjs["app.js<br/>editor · timer · autosave · results"]
        cdn["Monaco · marked · Split.js<br/>(CDN)"]
        appjs -.->|"loads"| cdn
    end

    subgraph server["Flask server — main.py"]
        routes["Pages + static (/ui)"]
        api["JSON API<br/>/api/formats<br/>/api/&lt;format&gt;/challenges<br/>/api/&lt;format&gt;/&lt;challenge&gt;/run/&lt;id&gt;/*"]
        gate["Stage gating<br/>read-only enforcement"]
    end

    subgraph core["src/"]
        fmt["formats/*.py<br/>ica · python_gym<br/>stages · whitelist · grading"]
        runner["runner_core.py<br/>discovery · subprocess runner"]
        runs["runs.py<br/>attempts: timer · progress<br/>code snapshot"]
        harness["test_harness.py<br/>unittest → JSON"]
    end

    subgraph storage["Storage"]
        lib[("challenges/&lt;format&gt;/&lt;id&gt;/<br/>statements · tests · template")]
        db[("challenges/progress.db<br/>SQLite")]
    end

    pages --> appjs
    appjs -->|"HTTP"| routes
    appjs -->|"fetch"| api
    api --> gate
    gate --> fmt
    gate --> runs
    gate -->|"discovery"| runner
    fmt -->|"run_modules"| runner
    runner -->|"subprocess"| harness
    runner -->|"reads challenge.json"| lib
    fmt -->|"read/write"| lib
    harness -->|"imports solution.py"| lib
    runs -->|"read/write"| db
```

The server is the only place that knows what is unlocked. The browser renders what it
is given; it never decides access.

## Responsibilities

| Component | Owns | Never does |
|---|---|---|
| `main.py` | Routing, stage gating, read-only enforcement, response shapes | Anything format-specific — no filenames, no "level" |
| `formats/*.py` | The challenge layout, which files are visible, the pass/fail gate, how much of a hidden failure is reported | Persistence, HTTP, knowing where the library lives |
| `runner_core.py` | Format + challenge discovery, spawning the harness | Persistence, format vocabulary |
| `runs.py` | Attempt rows: timer, progress, code snapshot, schema migration | Anything HTTP-aware |
| `test_harness.py` | Isolated subprocess: per-case time budget, output capture, JSON | Touching the DB |
| `ui/app.js` | Editor, tabs, timer display, autosave, result rendering | Deciding what is unlocked, or naming a stage itself |

## Running the tests for a stage

```mermaid
sequenceDiagram
    participant U as Browser
    participant A as main.py
    participant R as runs.py
    participant F as formats/ica.py
    participant C as runner_core.py
    participant H as test_harness.py

    U->>A: POST /run {stage, code}
    A->>A: reject if finished or stage locked
    A->>R: update_solution(run_id, code)
    A->>F: run_stage(cdir, stage, code)
    F->>F: materialize solution.py on disk
    F->>C: run_modules(cdir, level_1..N public + hidden)
    C->>H: subprocess, cwd=challenges/ica/<id>
    Note over H: each test case under<br/>ICA_CASE_TIMEOUT (SIGALRM)
    H-->>C: {"passed", "tests":[…]} on stdout
    C-->>F: parsed results
    F-->>A: {passed, public, hidden}
    alt result.passed
        A->>R: set_completed_stages(N) → unlocks N+1
        A->>R: mark_completed() if N was the last stage
    end
    A-->>U: results + unlocked stages + status
```

`main.py` never inspects `public`/`hidden` — the format decides `passed` and the rest is
passed through to the client. Hidden test **sources** never leave the server.

## Attempt lifecycle

```mermaid
stateDiagram-v2
    [*] --> in_progress: POST /runs (solution from template)
    state in_progress {
        [*] --> running
        running --> running: autosave, run tests
        running --> paused: leave the IDE
        paused --> running: POST /resume
    }
    in_progress --> completed: last stage passes
    completed --> [*]
```

The clock accumulates only while an attempt is *running*, so leaving the page pauses it.
The timebox is a target, not a lock: an in-progress attempt past its limit stays editable
and is simply flagged as over time. Completed attempts are read-only, enforced server-side.

## Challenge library

```mermaid
graph LR
    lib["challenges/"] --> ica["ica/"]
    lib --> gym["python-gym/"]

    ica --> c1["&lt;challenge_id&gt;/"]
    c1 --> meta1["challenge.json"]
    c1 --> l1["level_N.md · level_N_public_tests.py<br/>level_N_hidden_tests.py"]
    c1 --> t1["solution_template.py · solution.py"]

    gym --> c2["&lt;challenge_id&gt;/"]
    c2 --> meta2["challenge.json"]
    c2 --> l2["task.md · public_tests.py<br/>hidden_tests.py"]
    c2 --> t2["solution_template.py · solution.py"]
    c2 --> h2["gym_harness.py<br/>the challenge's own database"]
```

Only `challenge.json` is a core requirement — everything below it is the format's business,
which is why the two branches have different shapes. A challenge that needs a database
declares it itself (`gym_harness.py` builds an in-memory SQLite from the candidate's
models), so it can never reach `progress.db`. Adding a challenge means creating a folder;
there is no list to maintain anywhere.

## Trust boundaries

| Served to the browser | Never served |
|---|---|
| Statements of unlocked stages | Statements of locked stages |
| Public test sources | Hidden test sources |
| Your `solution.py` | `solution_template.py` |
| Hidden test *results* (names + status) | Hidden failure messages — for python-gym, which strips them; ICA still sends its tracebacks |

Enforced by the format's `read_file` whitelist (for ICA, `solution` and `public-<n>` are
the only addressable file ids) plus per-stage checks in `main.py`. Candidate code runs in
a subprocess with **no sandboxing** — keep the server on `127.0.0.1`.
