# Support Ticketing System

## Domain Overview

You are building the core of an in-memory support ticketing system. It tracks
support tickets, each identified by a string id and carrying an integer
**priority** (a higher number means a more urgent ticket). Over the next levels
the system will grow to support a ticket lifecycle (assignment and resolution),
history and workload analytics, and watcher notifications — but for now it only
needs to handle ticket creation and picking the next ticket to work on.

You implement everything in a single class, `TicketSystem`, in `solution.py`.
All priorities are non-negative integers.

---

## Level 1 Requirements

Implement the `TicketSystem` class with the following methods:

### `create_ticket(ticket_id: str, priority: int) -> bool`

Create a ticket with the given `priority` (you may assume `priority >= 0`). A new
ticket starts in the **`"open"`** status.

- Returns `True` if the ticket was created.
- Returns `False` if `ticket_id` already exists. In that case the existing ticket
  is **not** modified.

### `get_status(ticket_id: str) -> str | None`

Return the ticket's current status (for now always `"open"`), or `None` if no
ticket with that id exists.

### `get_priority(ticket_id: str) -> int | None`

Return the ticket's priority, or `None` if no ticket with that id exists.

### `next_ticket() -> str | None`

Return the id of the highest-priority ticket that is still **`"open"`**, **without
changing anything** (this is a peek, not a pop).

- Ties in priority are broken by **creation order**: the ticket created earliest
  wins.
- Returns `None` if there is no open ticket.
- (Later levels add ways for a ticket to leave the `"open"` status; once it does,
  it is no longer returned by `next_ticket`.)

---

## Hidden Tests Check For

- Creating a ticket returns `True`; a duplicate id returns `False` and does not
  overwrite the original priority/status.
- `get_status` of a new ticket is `"open"`; unknown ids return `None`.
- `get_priority` returns the exact priority; unknown ids return `None`.
- `next_ticket` returns the highest priority; a strictly higher priority always
  wins regardless of creation order.
- `next_ticket` breaks ties by earliest creation, not by id ordering.
- `next_ticket` returns `None` for an empty system.
- `next_ticket` is a peek: calling it repeatedly returns the same id and changes
  nothing.
- Priority `0` is a valid priority and participates normally.
