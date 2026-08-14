# Components

How the pieces of the ICA Mock Assessment fit together. See `README.md` for setup and
`AGENTS.md` for working rules.

## System overview

```mermaid
graph TB
    subgraph browser["Browser"]
        pages["Pages<br/>challenges · attempts · IDE"]
        appjs["app.js<br/>editor · timer · autosave · results"]
        cdn["Monaco · marked · Split.js<br/>(CDN)"]
        appjs -.->|"loads"| cdn
    end

    subgraph server["Flask server — main.py"]
        routes["Pages + static (/ui)"]
        api["JSON API<br/>/api/challenges<br/>/api/&lt;challenge&gt;/runs<br/>/api/&lt;challenge&gt;/run/&lt;id&gt;/*"]
        gate["Level gating<br/>read-only enforcement"]
    end

    subgraph core["src/"]
        runner["runner_core.py<br/>discovery · file whitelist<br/>test execution"]
        runs["runs.py<br/>attempts: timer · progress<br/>code snapshot"]
        harness["test_harness.py<br/>unittest → JSON"]
    end

    subgraph storage["Storage"]
        lib[("challenges/&lt;id&gt;/<br/>statements · tests · template")]
        db[("challenges/progress.db<br/>SQLite")]
    end

    pages --> appjs
    appjs -->|"HTTP"| routes
    appjs -->|"fetch"| api
    api --> gate
    gate --> runner
    gate --> runs
    runner -->|"subprocess"| harness
    runner -->|"read/write"| lib
    harness -->|"imports solution.py"| lib
    runs -->|"read/write"| db
```

The server is the only place that knows what is unlocked. The browser renders what it
is given; it never decides access.

## Responsibilities

| Component | Owns | Never does |
|---|---|---|
| `main.py` | Routing, gating, read-only enforcement, response shapes | Business logic of test running |
| `runner_core.py` | Challenge discovery, whitelisted file reads, spawning tests | Persistence |
| `runs.py` | Attempt rows: timer, progress, code snapshot, schema migration | Anything HTTP-aware |
| `test_harness.py` | Isolated subprocess: per-case time budget, output capture, JSON | Touching the DB |
| `ui/app.js` | Editor, tabs, timer display, autosave, result rendering | Deciding what is unlocked |

## Running the tests for a level

```mermaid
sequenceDiagram
    participant U as Browser
    participant A as main.py
    participant R as runs.py
    participant C as runner_core.py
    participant H as test_harness.py

    U->>A: POST /run {level, code}
    A->>A: reject if finished or level locked
    A->>R: update_solution(run_id, code)
    A->>C: write_solution() — sync disk with the run
    A->>C: run_public(level) + run_hidden(level)
    C->>H: subprocess, cwd=challenges/<id>
    Note over H: each test case under<br/>ICA_CASE_TIMEOUT (SIGALRM)
    H-->>C: {"passed", "tests":[…]} on stdout
    C-->>A: parsed results
    alt public AND hidden pass for levels 1..N
        A->>R: set_completed_level(N) → unlocks N+1
        A->>R: mark_completed() if N was the last level
    end
    A-->>U: results + unlocked levels + status
```

Hidden test **sources** never leave the server — only their pass/fail results do.

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
    in_progress --> completed: last level passes
    completed --> [*]
```

The clock accumulates only while an attempt is *running*, so leaving the page pauses it.
The timebox is a target, not a lock: an in-progress attempt past its limit stays editable
and is simply flagged as over time. Completed attempts are read-only, enforced server-side.

## Challenge library

```mermaid
graph LR
    lib["challenges/"] --> c["&lt;challenge_id&gt;/<br/><i>folder name = id = route</i>"]
    c --> meta["challenge.json<br/>title · timebox_minutes"]
    c --> tpl["solution_template.py<br/>starter, never served"]
    c --> sol["solution.py<br/>candidate's code (gitignored)"]
    c --> lvl["level_N.md<br/>statement"]
    c --> pub["level_N_public_tests.py<br/>shown read-only"]
    c --> hid["level_N_hidden_tests.py<br/>results only"]
```

Levels are discovered by globbing `level_*_public_tests.py`, and a challenge registers
itself simply by having a `challenge.json` — there is no list to maintain anywhere.

## Trust boundaries

| Served to the browser | Never served |
|---|---|
| Statements of unlocked levels | Statements of locked levels |
| Public test sources | Hidden test sources |
| Your `solution.py` | `solution_template.py` |
| Hidden test *results* (names + status) | — |

Enforced by a whitelist in `runner_core` (`solution` and `public-<n>` are the only
addressable file ids) plus per-level checks in `main.py`. Candidate code runs in a
subprocess with **no sandboxing** — keep the server on `127.0.0.1`.
