---
name: refactor
description: Refactor this project's code — moving/renaming modules, extracting seams, changing routes, payloads or the DB schema, reorganizing directories. Ends by updating README.md, AGENTS.md and COMPONENTS.md wherever the change made them wrong. Use whenever the task is a refactor rather than a new feature or a bug fix.
---

# Refactoring in this repo

The docs here describe structure, and structure is exactly what a refactor moves. A
refactor is not done when the code works — it is done when the code works **and** the
three documents below still describe reality.

## Finish every refactor with a documentation pass

| Document | Describes | Re-read it when you changed |
|---|---|---|
| `README.md` | What the app is, how to install and run it, how a user moves through it | The startup banner, env vars, URLs a user visits, directory layout, the vocabulary users see |
| `AGENTS.md` | The map for coding agents: layout, run/verify commands, invariants, conventions | Any file's role, a function named in an invariant, the API used in the curl examples, gitignore rules |
| `COMPONENTS.md` | Diagrams: system overview, request sequence, lifecycle, library layout, trust boundaries | Which module calls which, route or payload shapes, on-disk layout, who enforces what |

Also check, they go stale the same way:

- `.agents/skills/*/SKILL.md` — playbooks that name paths, ids or URLs (and mirror any
  frontmatter `description` change into the `.claude/skills/` stub).
- `prompt.md` — the ICA authoring spec, which names challenge paths.

## Judgment: update what drifted, nothing else

Only fix what the refactor made **wrong**. A section describing behavior you did not
touch stays exactly as it is — rewording it produces diff noise and buries the real
change. Two failure modes, both bad:

- Leaving a stale path, function name or route: the next agent trusts it and acts on a
  file that no longer exists.
- Rewriting prose that was already correct: reviewers can no longer see what moved.

When a doc names a symbol you renamed, the fix is the rename — not a new paragraph.

## Sweep for stale references

Grep the docs for what you moved. Names, paths and routes, not prose:

```bash
grep -rn "old_function_name\|old/path\|/old/route" README.md AGENTS.md COMPONENTS.md \
    prompt.md .agents/ .claude/
```

Run it for every symbol, file and URL segment the refactor touched. Renamed columns and
env vars count too.

## Verify the diagrams still render

`COMPONENTS.md` diagrams are Mermaid, and a syntax error silently renders as a broken
block on GitHub. After editing any diagram:

```bash
PUPPETEER_EXECUTABLE_PATH=/opt/google/chrome/chrome \
  npx --yes @mermaid-js/mermaid-cli@10 -i COMPONENTS.md -o /tmp/render-check.md
```

Keep the output path outside the repo: one SVG per chart is written next to it. It
prints one ✅ per chart; anything else is a parse error with a line number. Two traps
worth knowing: `&lt;`/`&gt;` entities break `sequenceDiagram` messages (use a literal
`<id>` there), and a diagram whose boxes end up disconnected usually means the arrows no
longer describe the real call flow — fix the arrows, not the layout.

## Before reporting done

- [ ] The three documents match the new structure.
- [ ] The grep sweep is clean.
- [ ] Mermaid renders (only if a diagram changed).
- [ ] `AGENTS.md`'s verification commands actually run as written against the new API.
