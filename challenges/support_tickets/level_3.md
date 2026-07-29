# Level 3 Requirements

The support team needs history and workload analytics. Extend the **same**
`TicketSystem` class.

## New methods

### `history(ticket_id: str) -> list[str] | None`

Return the full ordered list of statuses the ticket has held, from creation up to
and including its current status.

- A freshly created ticket has history `["open"]`.
- Every successful transition appends the new status. For example, a ticket that
  was assigned, resolved, and then reopened has history
  `["open", "in_progress", "resolved", "open"]` (reopening records another
  `"open"`).
- Failed transitions (rejected ones) add nothing.
- Returns `None` if the ticket does not exist.

### `tickets_by_status(status: str) -> list[str]`

Return the ids of all tickets **currently** in `status`, sorted in ascending
lexicographic order.

- Returns an empty list if none match (including for an unknown status string).

### `agent_workload(agent_id: str) -> int`

Return how many tickets are **currently** assigned to `agent_id` and still
`"in_progress"`.

- A ticket only counts while it is `"in_progress"`; once it is resolved, closed,
  or reopened (which clears the assignee) it no longer counts.
- Returns `0` if the agent has no such tickets.

### `busiest_agent() -> str | None`

Return the id of the agent with the most `"in_progress"` tickets assigned to them.

- Ties are broken by `agent_id` **ascending** (lexicographic).
- Returns `None` if no ticket is currently `"in_progress"`.

---

## Hidden Tests Check For

- `history` starts as `["open"]` and records each successful transition in order,
  including repeated `"open"` entries produced by `reopen`.
- Rejected transitions do not appear in `history`.
- `history` returns `None` for an unknown ticket.
- `tickets_by_status` returns only the currently-matching ids, sorted; unknown or
  empty statuses return `[]`.
- `tickets_by_status` reflects transitions (a ticket moves between the buckets).
- `agent_workload` counts only `in_progress` tickets for that agent and drops the
  count when a ticket is resolved/closed/reopened.
- `busiest_agent` picks the max by count, breaking ties by `agent_id` ascending,
  and returns `None` when nothing is in progress.
- Performance: a large number of tickets and transitions is handled efficiently
  (id lookups must not degrade to a linear scan per operation).
