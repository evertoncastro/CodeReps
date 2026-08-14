# Level 2 Requirements

Tickets now move through a **lifecycle**. Extend the **same** `TicketSystem`
class — do not rename or break the Level 1 methods.

A ticket has one of four statuses and may only move along these transitions:

```
open ──assign──▶ in_progress ──resolve──▶ resolved ──close──▶ closed
                                              │                  │
                                              └──── reopen ──────┘
                                                     (back to open)
```

Any transition **not** drawn above is invalid and must be rejected (the method
returns `False` and changes nothing). A newly created ticket is `"open"`.

## New methods

### `assign(ticket_id: str, agent_id: str) -> bool`

Assign an **open** ticket to `agent_id`, moving it to `"in_progress"`.

- Returns `True` on success.
- Returns `False`, changing nothing, if the ticket does not exist or is not
  currently `"open"`.

### `resolve(ticket_id: str) -> bool`

Move an **in_progress** ticket to `"resolved"`.

- Returns `False`, changing nothing, if the ticket does not exist or is not
  currently `"in_progress"`.

### `close(ticket_id: str) -> bool`

Move a **resolved** ticket to `"closed"`.

- Returns `False`, changing nothing, if the ticket does not exist or is not
  currently `"resolved"`.

### `reopen(ticket_id: str) -> bool`

Move a **resolved** or **closed** ticket back to `"open"`. Reopening **clears its
assignee** (the ticket becomes unassigned again).

- Returns `False`, changing nothing, if the ticket does not exist or is neither
  `"resolved"` nor `"closed"`.

### `get_assignee(ticket_id: str) -> str | None`

Return the id of the agent the ticket is currently assigned to, or `None` if the
ticket is unassigned or does not exist.

## Interaction with `next_ticket`

`next_ticket` still returns the highest-priority ticket **whose status is
`"open"`** (same tie-break as Level 1). Tickets that have been assigned, resolved,
or closed are not `"open"` and are therefore skipped — until they are reopened.

---

## Hidden Tests Check For

- The full happy path `open → in_progress → resolved → closed` succeeds and the
  status reflects each step.
- Every invalid transition is rejected and leaves the status unchanged, e.g.:
  resolve/close on an `open` ticket, assign on an `in_progress`/`resolved`/`closed`
  ticket, close on an `in_progress` ticket, reopen on an `open`/`in_progress`
  ticket.
- All transition methods return `False` for an unknown ticket id.
- `assign` records the assignee; `get_assignee` returns it; `reopen` clears it.
- A ticket cannot be assigned twice without an intervening reopen.
- After `reopen`, the ticket can be assigned again (to the same or a different
  agent).
- `next_ticket` skips non-open tickets and returns the highest-priority remaining
  open one; a reopened ticket becomes eligible again.
